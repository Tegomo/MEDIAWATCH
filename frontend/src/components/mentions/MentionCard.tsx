import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'
import { ExternalLink, Clock, Newspaper } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface MentionCardProps {
  mention: {
    id: string
    matched_text: string
    match_context: string
    sentiment_score: number
    sentiment_label: string
    visibility_score: number
    theme: string | null
    detected_at: string
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
  onClick: (id: string) => void
}

const sentimentConfig: Record<string, { label: string; color: 'success' | 'destructive' | 'secondary' }> = {
  positive: { label: 'Positif', color: 'success' },
  negative: { label: 'Négatif', color: 'destructive' },
  neutral: { label: 'Neutre', color: 'secondary' },
}

export default function MentionCard({ mention, onClick }: MentionCardProps) {
  const sentiment = sentimentConfig[mention.sentiment_label] || sentimentConfig.neutral
  const timeAgo = formatDistanceToNow(new Date(mention.detected_at), { addSuffix: true, locale: fr })

  return (
    <Card
      className="cursor-pointer transition-all hover:shadow-md hover:border-primary/30"
      onClick={() => onClick(mention.id)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Article title */}
            {mention.article && (
              <h3 className="font-medium leading-snug line-clamp-2">
                {mention.article.title}
              </h3>
            )}

            {/* Context excerpt */}
            <p className="mt-1.5 text-sm text-muted-foreground line-clamp-2">
              {mention.match_context}
            </p>

            {/* Meta row */}
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              {/* Source */}
              {mention.article?.source && (
                <span className="flex items-center gap-1">
                  <Newspaper className="h-3 w-3" />
                  {mention.article.source.name}
                </span>
              )}

              {/* Time */}
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {timeAgo}
              </span>

              {/* External link */}
              {mention.article && (
                <a
                  href={mention.article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-primary hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  <ExternalLink className="h-3 w-3" />
                  Source
                </a>
              )}
            </div>
          </div>

          {/* Badges column */}
          <div className="flex flex-col items-end gap-1.5 shrink-0">
            <Badge variant={sentiment.color}>{sentiment.label}</Badge>
            {mention.keyword && (
              <Badge variant="outline" className="text-xs">
                {mention.keyword.text}
              </Badge>
            )}
            {mention.theme && (
              <Badge variant="secondary" className="text-xs">
                {mention.theme}
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
