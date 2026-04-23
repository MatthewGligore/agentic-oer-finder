"""
LLM Client for OER identification and evaluation
Supports multiple LLM providers: OpenAI, Anthropic, etc.
"""
import os
import time
from typing import List, Dict, Optional
import logging
import requests
import re

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified interface for LLM providers"""
    
    def __init__(self, provider='openai', model=None):
        self.provider = provider.lower()
        self.model = model or self._get_default_model()
        self.client = self._initialize_client()

    @staticmethod
    def _is_usable_api_key(key: str) -> bool:
        """Return True only for non-placeholder keys.

        This prevents accidental calls with template/example keys.
        """
        if not key:
            return False

        normalized = key.strip().lower()
        placeholder_patterns = [
            'your_openai',
            'your_anthropic',
            'replace_me',
            'changeme',
            'placeholder',
            'example',
            'none',
            'null'
        ]
        return not any(pattern in normalized for pattern in placeholder_patterns)
    
    def _get_default_model(self) -> str:
        """Get default model for provider"""
        defaults = {
            'openai': 'gpt-4o',
            'anthropic': 'claude-3-5-sonnet-20241022',
            'ollama': 'llama3.2:3b',
            'openai-gpt4': 'gpt-4o',
            'openai-gpt3': 'gpt-3.5-turbo'
        }
        return defaults.get(self.provider, 'gpt-4o')
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        # Check if we should use no-API mode
        api_key = os.getenv('OPENAI_API_KEY', '').strip()
        anthropic_key = os.getenv('ANTHROPIC_API_KEY', '').strip()

        # Explicit no-api providers always bypass external API clients.
        if self.provider in {'no_api', 'no-api', 'builtin', 'local'}:
            logger.info("No-API provider selected. Using fallback suggestions only.")
            return 'no-api'

        # Local Ollama provider does not require cloud API keys.
        if self.provider == 'ollama':
            logger.info("Using local Ollama provider.")
            return 'ollama'

        api_key_usable = self._is_usable_api_key(api_key)
        anthropic_key_usable = self._is_usable_api_key(anthropic_key)
        
        # If no API keys provided, use no-API mode
        if not api_key_usable and not anthropic_key_usable:
            logger.info("No API keys found. Using no-API mode (fallback suggestions only).")
            return 'no-api'  # Special marker for no-API mode
        
        if self.provider == 'openai' or self.provider.startswith('openai'):
            try:
                from openai import OpenAI
                if not api_key_usable:
                    logger.warning("OPENAI_API_KEY not found. Using no-API mode.")
                    return 'no-api'
                return OpenAI(api_key=api_key)
            except ImportError:
                logger.warning("OpenAI package not installed. Using no-API mode.")
                return 'no-api'
            except Exception as e:
                logger.warning(f"Error initializing OpenAI client: {e}. Using no-API mode.")
                return 'no-api'
        
        elif self.provider == 'anthropic':
            try:
                import anthropic
                if not anthropic_key_usable:
                    logger.warning("ANTHROPIC_API_KEY not found. Using no-API mode.")
                    return 'no-api'
                return anthropic.Anthropic(api_key=anthropic_key)
            except ImportError:
                logger.warning("Anthropic package not installed. Using no-API mode.")
                return 'no-api'
            except Exception as e:
                logger.warning(f"Error initializing Anthropic client: {e}. Using no-API mode.")
                return 'no-api'
        
        else:
            logger.warning(f"Unsupported LLM provider: {self.provider}. Using no-API mode.")
            return 'no-api'
    
    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 2000) -> Optional[str]:
        """
        Generate a response from the LLM
        
        Args:
            prompt: User prompt
            system_prompt: System/instruction prompt
            max_tokens: Maximum tokens in response
        
        Returns:
            Generated text or None if error
        """
        # Handle no-API mode
        if self.client == 'no-api':
            logger.debug("No-API mode: Skipping LLM generation")
            return None
        
        if not self.client:
            logger.warning("LLM client not initialized. Using no-API mode.")
            return None
        
        try:
            if self.client == 'ollama':
                base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')
                timeout_seconds = int(os.getenv('OLLAMA_TIMEOUT_SECONDS', '45'))
                payload = {
                    "model": self.model,
                    "stream": False,
                    "messages": []
                }

                if system_prompt:
                    payload["messages"].append({"role": "system", "content": system_prompt})
                payload["messages"].append({"role": "user", "content": prompt})

                started = time.time()
                logger.info("Ollama generate start: model=%s timeout=%ss", self.model, timeout_seconds)
                response = requests.post(
                    f"{base_url}/api/chat",
                    json=payload,
                    timeout=timeout_seconds
                )
                response.raise_for_status()
                data = response.json()
                logger.info("Ollama generate complete in %.2fs", time.time() - started)
                return (data.get('message') or {}).get('content')

            if self.provider == 'openai' or self.provider.startswith('openai'):
                if not self.client:
                    logger.error("OpenAI client not initialized")
                    return None
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif self.provider == 'anthropic':
                if not self.client:
                    logger.error("Anthropic client not initialized")
                    return None
                
                messages = []
                if system_prompt:
                    # Anthropic uses system parameter
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        system=system_prompt,
                        messages=[{"role": "user", "content": prompt}]
                    )
                else:
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    )
                return response.content[0].text
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None

    def is_ollama_reachable(self) -> bool:
        """Check if local Ollama endpoint is reachable."""
        if self.client != 'ollama':
            return True
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=4)
            return response.ok
        except Exception:
            return False
    
    def identify_oer_resources(self, syllabus_info: Dict, alg_resources: List[Dict]) -> List[Dict]:
        """
        Use LLM to identify relevant OER resources from ALG Library based on syllabus
        
        Args:
            syllabus_info: Information about the course syllabus
            alg_resources: List of resources from ALG Library
        
        Returns:
            List of relevant OER resources with relevance scores
        """
        # If no-API mode, return resources directly with basic relevance
        if self.client == 'no-api' or not self.client:
            logger.info("No-API mode: Using direct resource matching")
            course_code = syllabus_info.get('course_code', '')
            course_lower = course_code.lower()
            
            # Simple keyword matching for relevance
            identified = []
            for resource in alg_resources[:10]:  # Limit to top 10
                title = resource.get('title', '').lower()
                description = resource.get('description', '').lower()
                
                # Check if course subject appears in resource
                subject = course_code.split()[0].lower() if ' ' in course_code else course_lower
                relevance = f'Resource from Open ALG Library for {course_code}'
                
                if subject in title or subject in description:
                    relevance = f'Directly relevant to {course_code} - matches course subject'
                
                identified.append({
                    'resource': resource,
                    'relevance_explanation': relevance,
                    'identified_by': 'direct_matching'
                })
            
            return identified if identified else [
                {
                    'resource': r,
                    'relevance_explanation': f'OER resource for {course_code}',
                    'identified_by': 'direct'
                } for r in alg_resources[:5]
            ]
        
        system_prompt = """You are an expert in identifying open educational resources (OER) that match course requirements.
Analyze the course syllabus information and evaluate which resources from the ALG Library are most relevant.
Consider: course topics, learning objectives, required materials, and pedagogical needs."""
        
        prompt = f"""Course Syllabus Information:
Course: {syllabus_info.get('course_code', 'Unknown')}
Title: {syllabus_info.get('title', 'N/A')}
Description: {syllabus_info.get('description', 'N/A')[:1000]}

Available ALG Library Resources:
{self._format_resources_for_prompt(alg_resources[:20])}  # Limit to first 20 for token efficiency

Task: Identify the top 5-10 most relevant OER resources for this course. For each resource, provide:
1. Resource title
2. Relevance score (1-10)
3. Brief explanation of why it's relevant
4. How it could be integrated into the course

Format your response as a structured list."""
        
        response = self.generate(prompt, system_prompt, max_tokens=3000)
        
        if response:
            return self._parse_oer_identification(response, alg_resources)
        return []
    
    def evaluate_oer_quality(self, resource: Dict, rubric_criteria: List[str], syllabus_info: Dict = None) -> Dict:
        """
        Evaluate an OER resource using the quality rubric
        
        Args:
            resource: OER resource information
            rubric_criteria: List of rubric criteria to evaluate
        
        Returns:
            Evaluation results with scores and explanations
        """
        # If no-API mode, return empty evaluation (will use rule-based evaluation)
        if self.client == 'no-api' or not self.client:
            logger.debug("No-API mode: Using rule-based evaluation only")
            return {}  # Empty dict - rubric evaluator will handle it
        
        system_prompt = """You are an expert evaluator of open educational resources.
Evaluate resources using the OER quality rubric criteria.
Provide scores (1-5 scale) and detailed explanations for each criterion."""
        
        syllabus_context = ''
        if syllabus_info:
            sections = syllabus_info.get('sections') or {}
            section_lines = []
            for section_name, content in list(sections.items())[:5]:
                section_lines.append(f"- {section_name}: {str(content)[:240]}")
            syllabus_context = f"""
Syllabus Context:
Course: {syllabus_info.get('course_code', 'N/A')}
Course Title: {syllabus_info.get('course_title') or syllabus_info.get('title', 'N/A')}
Description: {str(syllabus_info.get('description', ''))[:400]}
Key Sections:
{chr(10).join(section_lines) if section_lines else '- No parsed sections available.'}
"""

        prompt = f"""Evaluate this OER resource using the quality rubric:

{syllabus_context}

Resource Information:
Title: {resource.get('title', 'N/A')}
Description: {resource.get('description', 'N/A')[:1000]}
License: {resource.get('license', 'N/A')}
Author: {resource.get('author', 'N/A')}
URL: {resource.get('url', 'N/A')}

Rubric Criteria to Evaluate:
{chr(10).join(f'- {criterion}' for criterion in rubric_criteria)}

For each criterion, provide:
1. Score (1-5, where 5 is excellent)
2. Detailed explanation
3. Evidence from both the resource information and syllabus context

Also provide:
- Overall quality score
- Strengths
- Weaknesses
- Recommendations for use

Format your response as structured JSON if possible, or as a clear structured text."""
        
        response = self.generate(prompt, system_prompt, max_tokens=2000)
        
        if response:
            return self._parse_evaluation(response, resource, rubric_criteria)
        return {}

    def evaluate_syllabus_relevance(self, resource: Dict, syllabus_context: Dict) -> Dict:
        """Score semantic relevance between a resource and syllabus-derived context."""
        title = (resource or {}).get('title', '')
        description = (resource or {}).get('description', '')

        course_title = (syllabus_context or {}).get('course_title', '')
        course_description = (syllabus_context or {}).get('course_description', '')
        objectives = (syllabus_context or {}).get('objectives', [])
        topics = (syllabus_context or {}).get('topics', [])

        if self.client == 'no-api' or not self.client:
            return self._fallback_relevance(resource, syllabus_context)

        system_prompt = (
            "You evaluate how well an OER resource aligns to a course syllabus. "
            "Return plain text with exactly these lines: score: <1-5>, matched_topics: <comma list>, rationale: <short reason>."
        )

        prompt = f"""Syllabus Context:
Course title: {course_title}
Course description: {course_description[:650]}
Objectives: {', '.join(objectives[:8])}
Topics: {', '.join(topics[:12])}

Resource:
Title: {title}
Description: {description[:900]}
URL: {(resource or {}).get('url', '')}

Score this resource for syllabus fit on a 1-5 scale.
"""

        response = self.generate(prompt, system_prompt=system_prompt, max_tokens=300)
        if not response:
            return self._fallback_relevance(resource, syllabus_context)

        score = 3.0
        matched_topics: List[str] = []
        rationale = 'LLM relevance evaluation completed.'

        score_match = re.search(r'score\s*:\s*([1-5](?:\.\d+)?)', response, flags=re.IGNORECASE)
        if score_match:
            score = float(score_match.group(1))

        topics_match = re.search(r'matched_topics\s*:\s*(.+)', response, flags=re.IGNORECASE)
        if topics_match:
            raw = topics_match.group(1).strip()
            matched_topics = [item.strip() for item in raw.split(',') if item.strip()][:8]

        rationale_match = re.search(r'rationale\s*:\s*(.+)', response, flags=re.IGNORECASE)
        if rationale_match:
            rationale = rationale_match.group(1).strip()

        return {
            'score': max(1.0, min(5.0, score)),
            'matched_topics': matched_topics,
            'rationale': rationale,
            'raw': response,
        }

    def _fallback_relevance(self, resource: Dict, syllabus_context: Dict) -> Dict:
        """Rule-based relevance fallback for no-API mode."""
        title = (resource or {}).get('title', '')
        url = (resource or {}).get('url', '')
        description = (resource or {}).get('description', '')
        search_profile = (syllabus_context or {}).get('search_profile', {}) or {}

        # Ignore synthetic scraper blurbs that mirror the query and can create false positives.
        synthetic = 'candidate resource from' in str(description).lower() or 'search for' in str(title).lower()
        text = f"{title} {' ' if synthetic else description}".lower()

        if 'search for' in title.lower() or '/search' in str(url).lower():
            return {
                'score': 1.2,
                'matched_topics': [],
                'rationale': 'Generic source search listing; down-ranked against direct resource pages.',
            }

        if any(
            phrase in f"{title} {description}".lower()
            for phrase in [
                'research grant',
                'research report',
                'adoption of',
                'standard operating procedures',
                'kick-off training',
                'promotion and tenure',
            ]
        ):
            return {
                'score': 1.0,
                'matched_topics': [],
                'rationale': 'Program or administrative resource; down-ranked against direct course materials.',
            }

        topic_terms = [str(t).strip().lower() for t in (syllabus_context or {}).get('topics', []) if str(t).strip()]
        objective_terms = [str(t).strip().lower() for t in (syllabus_context or {}).get('objectives', []) if str(t).strip()]
        profile_terms = [str(t).strip().lower() for t in search_profile.get('required_terms', []) if str(t).strip()]
        terms = list(dict.fromkeys(profile_terms + topic_terms + objective_terms))[:25]

        if not terms:
            return {'score': 3.0, 'matched_topics': [], 'rationale': 'No syllabus topics/objectives available for relevance scoring.'}

        matched = [term for term in terms if term in text]
        ratio = len(matched) / max(1, min(len(terms), 12))
        score = 1.0 + (4.0 * min(1.0, ratio))

        if search_profile.get('strict_matching'):
            preferred_phrase_match = any(
                phrase.lower() in text
                for phrase in search_profile.get('preferred_queries', [])
                if phrase
            )
            required_matches = sum(1 for term in profile_terms if term in text)
            if not preferred_phrase_match and required_matches < 2:
                score = min(score, 1.6)

        url_lower = str(url).lower()
        if any(token in url_lower for token in ['/merlot/viewmaterial', 'materials.htm?materialid=', '/projects/', '/courseware/']):
            score += 0.7
        if any(host in url_lower for host in ['meshresearch.net', 'commons.msu.edu', 'hcommons.org']):
            score -= 1.0

        return {
            'score': round(max(1.0, min(5.0, score)), 2),
            'matched_topics': matched[:8],
            'rationale': f'Fallback relevance using topic/objective term overlap ({len(matched)} matches).',
        }
    
    def _format_resources_for_prompt(self, resources: List[Dict]) -> str:
        """Format resources list for LLM prompt"""
        formatted = []
        for i, resource in enumerate(resources, 1):
            formatted.append(f"""
{i}. {resource.get('title', 'Untitled')}
   Description: {resource.get('description', 'N/A')[:300]}
   License: {resource.get('license', 'Unknown')}
   URL: {resource.get('url', 'N/A')}
""")
        return '\n'.join(formatted)
    
    def _parse_oer_identification(self, response: str, alg_resources: List[Dict]) -> List[Dict]:
        """Parse LLM response into structured resource list"""
        # This is a simplified parser - can be enhanced
        identified = []
        
        # Try to extract resource titles and match them to ALG resources
        lines = response.split('\n')
        current_resource = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for resource titles
            for resource in alg_resources:
                if resource['title'].lower() in line.lower():
                    identified.append({
                        'resource': resource,
                        'relevance_explanation': line,
                        'identified_by': 'llm'
                    })
                    break
        
        # If parsing fails, return top resources with LLM explanation
        if not identified and alg_resources:
            identified = [{
                'resource': resource,
                'relevance_explanation': response[:200],
                'identified_by': 'llm'
            } for resource in alg_resources[:5]]
        
        return identified
    
    def _parse_evaluation(self, response: str, resource: Dict, rubric_criteria: List[str]) -> Dict:
        """Parse evaluation response into structured format"""
        evaluation = {
            'resource': resource,
            'criteria_scores': {},
            'overall_score': 0,
            'strengths': [],
            'weaknesses': [],
            'recommendations': [],
            'evaluation_text': response
        }
        
        # Try to extract scores for each criterion
        for criterion in rubric_criteria:
            # Look for criterion mentions in response
            criterion_lower = criterion.lower()
            if criterion_lower in response.lower():
                # Try to extract score (look for numbers near criterion name)
                pattern = rf'{re.escape(criterion)}[:\s]+(\d+)'
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    evaluation['criteria_scores'][criterion] = int(match.group(1))
        
        # Extract overall score
        overall_match = re.search(r'overall[:\s]+(\d+)', response, re.IGNORECASE)
        if overall_match:
            evaluation['overall_score'] = int(overall_match.group(1))
        
        return evaluation
