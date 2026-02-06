import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/badge'
import { Newspaper } from 'lucide-react'
import api from '@/services/api'

interface Source {
  id: string
  name: string
}

interface SourceFilterProps {
  selectedSourceId: string | null
  onSourceChange: (sourceId: string | null) => void
}

export default function SourceFilter({ selectedSourceId, onSourceChange }: SourceFilterProps) {
  const { data: sources } = useQuery<Source[]>({
    queryKey: ['sources-list'],
    queryFn: async () => {
      const resp = await api.get<{ sources: Source[] }>('/analytics/sources?days=90')
      return resp.data.sources.map((s) => ({ id: s.name, name: s.name }))
    },
    staleTime: 5 * 60 * 1000,
  })

  if (!sources || sources.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <Newspaper className="h-3.5 w-3.5 text-muted-foreground" />
      {sources.map((source) => (
        <Badge
          key={source.id}
          variant={selectedSourceId === source.name ? 'default' : 'outline'}
          className="cursor-pointer text-xs"
          onClick={() =>
            onSourceChange(selectedSourceId === source.name ? null : source.name)
          }
        >
          {source.name}
        </Badge>
      ))}
    </div>
  )
}
