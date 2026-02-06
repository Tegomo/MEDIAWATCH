import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { X, ExternalLink, Newspaper, Clock, User, Tag, BarChart3 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import api from '@/services/api'

interface MentionDetail {
  id: string
  matched_text: string
  match_context: string
  sentiment_score: number
  sentiment_label: string
  visibility_score: number
  theme: string | null
  detected_at: string
  extracted_entities: Record<string, unknown> | null
  article_content: string | null
  keyword: { id: string; text: string; category: string } | null
  article: {
    id: string
    title: string
    url: string
    author: string | null
    published_at: string
    source: { id: string; name: string; url: string; type: string } | null
  } | null
}

interface MentionDetailModalProps {
  mentionId: string | null
  onClose: () => void
}

const sentimentConfig: Record<string, { label: string; color: 'success' | 'destructive' | 'secondary'; emoji: string }> = {
  positive: { label: 'Positif', color: 'success', emoji: '+' },
  negative: { label: 'Négatif', color: 'destructive', emoji: '-' },
  neutral: { label: 'Neutre', color: 'secondary', emoji: '~' },
}

export default function MentionDetailModal({ mentionId, onClose }: MentionDetailModalProps) {
  const [mention, setMention] = useState<MentionDetail | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (!mentionId) {
      setMention(null)
      return
    }

    const fetchMention = async () => {
      setIsLoading(true)
      try {
        const response = await api.get<MentionDetail>(`/mentions/${mentionId}`)
        setMention(response.data)
      } catch {
        setMention(null)
      } finally {
        setIsLoading(false)
      }
    }

    fetchMention()
  }, [mentionId])

  if (!mentionId) return null

  const sentiment = sentimentConfig[mention?.sentiment_label || 'neutral'] || sentimentConfig.neutral

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="relative mx-4 max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-background shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-background p-4">
          <h2 className="text-lg font-semibold">Détail de la mention</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center p-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : mention ? (
          <div className="p-4 space-y-6">
            {/* Article title */}
            {mention.article && (
              <div>
                <h3 className="text-xl font-semibold leading-tight">{mention.article.title}</h3>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                  {mention.article.source && (
                    <span className="flex items-center gap-1">
                      <Newspaper className="h-4 w-4" />
                      {mention.article.source.name}
                    </span>
                  )}
                  {mention.article.author && (
                    <span className="flex items-center gap-1">
                      <User className="h-4 w-4" />
                      {mention.article.author}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {format(new Date(mention.article.published_at), 'dd MMM yyyy HH:mm', { locale: fr })}
                  </span>
                  <a
                    href={mention.article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-primary hover:underline"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Voir l'article original
                  </a>
                </div>
              </div>
            )}

            {/* Sentiment & metadata */}
            <div className="flex flex-wrap gap-2">
              <Badge variant={sentiment.color} className="gap-1">
                <BarChart3 className="h-3 w-3" />
                {sentiment.label} ({(mention.sentiment_score * 100).toFixed(0)}%)
              </Badge>
              {mention.keyword && (
                <Badge variant="outline" className="gap-1">
                  <Tag className="h-3 w-3" />
                  {mention.keyword.text}
                </Badge>
              )}
              {mention.theme && (
                <Badge variant="secondary">{mention.theme}</Badge>
              )}
              <Badge variant="outline">
                Visibilité: {(mention.visibility_score * 100).toFixed(0)}%
              </Badge>
            </div>

            {/* Match context */}
            <div>
              <h4 className="mb-2 text-sm font-medium text-muted-foreground">Contexte de la mention</h4>
              <div className="rounded-md bg-muted/50 p-3 text-sm leading-relaxed">
                {mention.match_context}
              </div>
            </div>

            {/* Full article content */}
            {mention.article_content && (
              <div>
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">Contenu de l'article</h4>
                <div className="max-h-64 overflow-y-auto rounded-md border p-3 text-sm leading-relaxed">
                  {mention.article_content}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-12 text-center text-muted-foreground">
            Mention non trouvée
          </div>
        )}
      </div>
    </div>
  )
}
