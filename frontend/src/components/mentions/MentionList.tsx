import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import MentionCard from './MentionCard'

interface Mention {
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

interface MentionListProps {
  mentions: Mention[]
  total: number
  limit: number
  offset: number
  onPageChange: (newOffset: number) => void
  onMentionClick: (id: string) => void
}

export default function MentionList({
  mentions,
  total,
  limit,
  offset,
  onPageChange,
  onMentionClick,
}: MentionListProps) {
  const currentPage = Math.floor(offset / limit) + 1
  const totalPages = Math.ceil(total / limit)
  const hasPrev = offset > 0
  const hasNext = offset + limit < total

  if (mentions.length === 0) {
    return null
  }

  return (
    <div className="space-y-3">
      {mentions.map((mention) => (
        <MentionCard key={mention.id} mention={mention} onClick={onMentionClick} />
      ))}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4">
          <p className="text-sm text-muted-foreground">
            {offset + 1}-{Math.min(offset + limit, total)} sur {total} mentions
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!hasPrev}
              onClick={() => onPageChange(Math.max(0, offset - limit))}
            >
              <ChevronLeft className="h-4 w-4" />
              Précédent
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {currentPage}/{totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={!hasNext}
              onClick={() => onPageChange(offset + limit)}
            >
              Suivant
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
