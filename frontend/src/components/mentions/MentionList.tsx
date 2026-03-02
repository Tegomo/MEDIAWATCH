import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'
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

function getPageNumbers(currentPage: number, totalPages: number): (number | 'ellipsis')[] {
  const pages: (number | 'ellipsis')[] = []
  const delta = 1

  pages.push(1)

  const rangeStart = Math.max(2, currentPage - delta)
  const rangeEnd = Math.min(totalPages - 1, currentPage + delta)

  if (rangeStart > 2) pages.push('ellipsis')

  for (let i = rangeStart; i <= rangeEnd; i++) {
    pages.push(i)
  }

  if (rangeEnd < totalPages - 1) pages.push('ellipsis')

  if (totalPages > 1) pages.push(totalPages)

  return pages
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

  const pageNumbers = getPageNumbers(currentPage, totalPages)

  return (
    <div className="space-y-3">
      {mentions.map((mention) => (
        <MentionCard key={mention.id} mention={mention} onClick={onMentionClick} />
      ))}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t pt-4">
          <p className="text-sm text-muted-foreground">
            {offset + 1}–{Math.min(offset + limit, total)} sur {total} mentions
          </p>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              disabled={!hasPrev}
              onClick={() => onPageChange(0)}
              title="Première page"
            >
              <ChevronsLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              disabled={!hasPrev}
              onClick={() => onPageChange(Math.max(0, offset - limit))}
              title="Page précédente"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>

            {pageNumbers.map((page, idx) =>
              page === 'ellipsis' ? (
                <span key={`ellipsis-${idx}`} className="px-1 text-sm text-muted-foreground">
                  …
                </span>
              ) : (
                <Button
                  key={page}
                  variant={page === currentPage ? 'default' : 'outline'}
                  size="icon"
                  className="h-8 w-8 text-xs"
                  onClick={() => onPageChange((page - 1) * limit)}
                >
                  {page}
                </Button>
              )
            )}

            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              disabled={!hasNext}
              onClick={() => onPageChange(offset + limit)}
              title="Page suivante"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              disabled={!hasNext}
              onClick={() => onPageChange((totalPages - 1) * limit)}
              title="Dernière page"
            >
              <ChevronsRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
