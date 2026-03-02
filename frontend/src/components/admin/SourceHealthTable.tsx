import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { RefreshCw, ExternalLink, Loader2, Pencil, Trash2 } from 'lucide-react'
import SourceStatusBadge from './SourceStatusBadge'
import api from '@/services/api'

interface SourceHealth {
  id: string
  name: string
  url: string
  type: string
  scraper_class: string
  scraping_enabled: boolean
  prestige_score: number
  status: 'ok' | 'warning' | 'error' | 'disabled'
  consecutive_failures: number
  last_scrape_at: string | null
  last_success_at: string | null
  last_error_message: string | null
  articles_24h: number
  total_articles: number
}

interface SourceHealthTableProps {
  sources: SourceHealth[]
  onRefresh: () => void
  onEdit: (source: SourceHealth) => void
  onDelete: (sourceId: string, sourceName: string) => void
}

export default function SourceHealthTable({ sources, onRefresh, onEdit, onDelete }: SourceHealthTableProps) {
  const [retryingId, setRetryingId] = useState<string | null>(null)

  const handleRetry = async (sourceId: string) => {
    setRetryingId(sourceId)
    try {
      await api.post(`/admin/sources/${sourceId}/retry`)
      onRefresh()
    } catch {
      // silently fail
    } finally {
      setRetryingId(null)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—'
    const d = new Date(dateStr)
    return d.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Source</th>
                <th className="px-4 py-3 text-left font-medium">Statut</th>
                <th className="px-4 py-3 text-center font-medium">Articles (24h)</th>
                <th className="px-4 py-3 text-center font-medium">Total</th>
                <th className="px-4 py-3 text-center font-medium">Échecs</th>
                <th className="px-4 py-3 text-left font-medium">Dernier scraping</th>
                <th className="px-4 py-3 text-left font-medium">Dernier succès</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source) => (
                <tr key={source.id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <div className="flex flex-col">
                      <span className="font-medium">{source.name}</span>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-primary"
                      >
                        {source.url.replace(/^https?:\/\//, '').split('/')[0]}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <SourceStatusBadge status={source.status} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={source.articles_24h > 0 ? 'font-medium text-green-600' : 'text-muted-foreground'}>
                      {source.articles_24h}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-muted-foreground">
                    {source.total_articles}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={source.consecutive_failures > 0 ? 'font-medium text-red-600' : 'text-muted-foreground'}>
                      {source.consecutive_failures}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {formatDate(source.last_scrape_at)}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {formatDate(source.last_success_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(source)}
                        className="h-7 w-7 p-0"
                        title="Modifier"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      {(source.status === 'error' || source.status === 'disabled') && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRetry(source.id)}
                          disabled={retryingId === source.id}
                          className="h-7 gap-1 text-xs"
                        >
                          {retryingId === source.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <RefreshCw className="h-3 w-3" />
                          )}
                          Retry
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(source.id, source.name)}
                        className="h-7 w-7 p-0 text-red-500 hover:text-red-700"
                        title="Supprimer"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
