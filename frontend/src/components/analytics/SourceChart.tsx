import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface SourceData {
  name: string
  type: string
  mention_count: number
  avg_sentiment: number
}

interface SourceChartProps {
  data: SourceData[]
  isLoading?: boolean
}

const getSentimentColor = (avgSentiment: number): string => {
  if (avgSentiment > 0.1) return '#22c55e'
  if (avgSentiment < -0.1) return '#ef4444'
  return '#a1a1aa'
}

export default function SourceChart({ data, isLoading }: SourceChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Mentions par source</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-[300px] items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Mentions par source</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-[300px] flex-col items-center justify-center text-muted-foreground">
            <p className="text-sm font-medium">Aucune donnée disponible</p>
            <p className="mt-1 text-xs">Les sources apparaîtront après le premier scraping</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-medium">Mentions par source</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11 }} />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 11 }}
              width={120}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
                fontSize: '12px',
              }}
            />
            <Bar dataKey="mention_count" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell key={index} fill={getSentimentColor(entry.avg_sentiment)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
