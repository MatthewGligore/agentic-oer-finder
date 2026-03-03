import React from 'react'
import Card from './ui/Card'
import Button from './ui/Button'

function Results({ data }) {
  const resources = data?.evaluated_resources || []

  if (resources.length === 0) {
    return (
      <Card className="p-8 text-center text-slate-600 dark:text-slate-300">
        <p>No resources found for this course. Try a different course code.</p>
      </Card>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h3 className="text-xl font-semibold tracking-tight text-slate-800 dark:text-slate-100">Found {resources.length} Resource{resources.length !== 1 ? 's' : ''}</h3>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {resources.map((item, index) => {
          const resource = item.resource || item
          const title = resource.title || resource.name || 'Untitled Resource'
          const url = resource.url || resource.link || '#'
          const description = resource.description || 'No description available'
          const rubricScore = item.rubric_evaluation?.score || 0
          const licenseInfo = item.license_check?.license || 'Unknown License'

          return (
            <Card key={index} className="flex h-full flex-col transition hover:-translate-y-0.5 hover:shadow-md">
              <div className="px-6 pb-0 pt-6">
                <h4 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  <a className="text-brand-600 hover:text-brand-700 hover:underline" href={url} target="_blank" rel="noopener noreferrer">
                    {title}
                  </a>
                </h4>
              </div>

              <div className="flex-1 p-6">
                <p className="mb-4 text-sm leading-6 text-slate-600 dark:text-slate-300">{description}</p>

                <div className="mb-4 flex flex-wrap gap-2">
                  {rubricScore > 0 && (
                    <div className="rounded-md bg-brand-100 px-3 py-1 text-xs font-medium text-brand-700">
                      Quality Score: <strong>{rubricScore.toFixed(1)}/100</strong>
                    </div>
                  )}
                  <div className="rounded-md bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-200">{licenseInfo}</div>
                </div>

                {item.integration_guidance && (
                  <div className="rounded border-l-4 border-brand-500 bg-slate-50 p-4 text-sm dark:bg-slate-900/60">
                    <strong className="mb-1 block text-slate-900 dark:text-slate-100">Integration Tips</strong>
                    <p className="text-slate-600 dark:text-slate-300">{item.integration_guidance}</p>
                  </div>
                )}
              </div>

              <div className="border-t border-slate-100 px-6 pb-6 pt-4 dark:border-slate-700/60">
                <Button
                  as="a"
                  className="w-full"
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Visit Resource →
                </Button>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

export default Results
