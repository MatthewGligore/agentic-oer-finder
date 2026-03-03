"""
LLM Client for OER identification and evaluation
Supports multiple LLM providers: OpenAI, Anthropic, etc.
"""
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified interface for LLM providers"""
    
    def __init__(self, provider='openai', model=None):
        self.provider = provider.lower()
        self.model = model or self._get_default_model()
        self.client = self._initialize_client()
    
    def _get_default_model(self) -> str:
        """Get default model for provider"""
        defaults = {
            'openai': 'gpt-4o',
            'anthropic': 'claude-3-5-sonnet-20241022',
            'openai-gpt4': 'gpt-4o',
            'openai-gpt3': 'gpt-3.5-turbo'
        }
        return defaults.get(self.provider, 'gpt-4o')
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        # Check if we should use no-API mode
        api_key = os.getenv('OPENAI_API_KEY', '')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
        
        # If no API keys provided, use no-API mode
        if not api_key and not anthropic_key:
            logger.info("No API keys found. Using no-API mode (fallback suggestions only).")
            return 'no-api'  # Special marker for no-API mode
        
        if self.provider == 'openai' or self.provider.startswith('openai'):
            try:
                from openai import OpenAI
                if not api_key:
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
                if not anthropic_key:
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
    
    def evaluate_oer_quality(self, resource: Dict, rubric_criteria: List[str]) -> Dict:
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
        
        prompt = f"""Evaluate this OER resource using the quality rubric:

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
3. Evidence from the resource information

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
                import re
                pattern = rf'{re.escape(criterion)}[:\s]+(\d+)'
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    evaluation['criteria_scores'][criterion] = int(match.group(1))
        
        # Extract overall score
        import re
        overall_match = re.search(r'overall[:\s]+(\d+)', response, re.IGNORECASE)
        if overall_match:
            evaluation['overall_score'] = int(overall_match.group(1))
        
        return evaluation
