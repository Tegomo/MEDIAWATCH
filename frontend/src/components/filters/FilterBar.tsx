import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Search, X, SlidersHorizontal } from 'lucide-react'
import DateRangePicker from './DateRangePicker'
import SentimentFilter from './SentimentFilter'

const THEME_OPTIONS = [
  { value: 'POLITICS', label: 'Politique' },
  { value: 'ECONOMY', label: 'Économie' },
  { value: 'SPORT', label: 'Sport' },
  { value: 'SOCIETY', label: 'Société' },
  { value: 'TECHNOLOGY', label: 'Technologie' },
  { value: 'CULTURE', label: 'Culture' },
  { value: 'OTHER', label: 'Autre' },
]

export interface Filters {
  search: string
  sentiment: string | null
  dateFrom: string
  dateTo: string
  theme: string | null
}

interface FilterBarProps {
  filters: Filters
  onFiltersChange: (filters: Filters) => void
  onSearch: () => void
  onClear: () => void
}

export const EMPTY_FILTERS: Filters = {
  search: '',
  sentiment: null,
  dateFrom: '',
  dateTo: '',
  theme: null,
}

export function hasActiveFilters(filters: Filters): boolean {
  return !!(
    filters.search ||
    filters.sentiment ||
    filters.dateFrom ||
    filters.dateTo ||
    filters.theme
  )
}

export default function FilterBar({ filters, onFiltersChange, onSearch, onClear }: FilterBarProps) {
  const update = (partial: Partial<Filters>) => {
    onFiltersChange({ ...filters, ...partial })
  }

  const activeCount = [
    filters.sentiment,
    filters.dateFrom || filters.dateTo,
    filters.theme,
  ].filter(Boolean).length

  return (
    <div className="space-y-3">
      {/* Row 1: Search + clear */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher dans les mentions..."
            value={filters.search}
            onChange={(e) => update({ search: e.target.value })}
            onKeyDown={(e) => e.key === 'Enter' && onSearch()}
            className="pl-8"
          />
        </div>
        <Button onClick={onSearch} variant="secondary" size="icon">
          <Search className="h-4 w-4" />
        </Button>
        {hasActiveFilters(filters) && (
          <Button onClick={onClear} variant="outline" size="sm" className="gap-1.5">
            <X className="h-3.5 w-3.5" />
            Effacer
            {activeCount > 0 && (
              <Badge variant="secondary" className="ml-1 h-5 w-5 rounded-full p-0 text-[10px]">
                {activeCount}
              </Badge>
            )}
          </Button>
        )}
      </div>

      {/* Row 2: Filter chips */}
      <div className="flex flex-wrap items-center gap-3">
        <SlidersHorizontal className="h-3.5 w-3.5 text-muted-foreground" />

        {/* Sentiment */}
        <SentimentFilter
          selected={filters.sentiment}
          onChange={(s) => update({ sentiment: s })}
        />

        <div className="h-4 w-px bg-border" />

        {/* Theme */}
        <div className="flex flex-wrap items-center gap-1.5">
          {THEME_OPTIONS.map((t) => (
            <Badge
              key={t.value}
              variant={filters.theme === t.value ? 'default' : 'outline'}
              className="cursor-pointer text-xs"
              onClick={() => update({ theme: filters.theme === t.value ? null : t.value })}
            >
              {t.label}
            </Badge>
          ))}
        </div>

        <div className="h-4 w-px bg-border" />

        {/* Date range */}
        <DateRangePicker
          dateFrom={filters.dateFrom}
          dateTo={filters.dateTo}
          onDateFromChange={(v) => update({ dateFrom: v })}
          onDateToChange={(v) => update({ dateTo: v })}
        />
      </div>
    </div>
  )
}
