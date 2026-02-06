import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface SentimentFilterProps {
  selected: string | null
  onChange: (sentiment: string | null) => void
}

const SENTIMENTS = [
  { value: 'POSITIVE', label: 'Positif', icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-100 border-green-300' },
  { value: 'NEUTRAL', label: 'Neutre', icon: Minus, color: 'text-gray-600', bg: 'bg-gray-100 border-gray-300' },
  { value: 'NEGATIVE', label: 'Négatif', icon: TrendingDown, color: 'text-red-600', bg: 'bg-red-100 border-red-300' },
]

export default function SentimentFilter({ selected, onChange }: SentimentFilterProps) {
  return (
    <div className="flex items-center gap-1.5">
      {SENTIMENTS.map((s) => {
        const Icon = s.icon
        const isActive = selected === s.value
        return (
          <Badge
            key={s.value}
            variant="outline"
            className={`cursor-pointer gap-1 text-xs transition-colors ${
              isActive ? s.bg : 'hover:bg-muted'
            }`}
            onClick={() => onChange(isActive ? null : s.value)}
          >
            <Icon className={`h-3 w-3 ${isActive ? s.color : 'text-muted-foreground'}`} />
            {s.label}
          </Badge>
        )
      })}
    </div>
  )
}
