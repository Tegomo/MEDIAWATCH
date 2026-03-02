import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface TrendDataPoint {
  date: string
  total: number
  positive: number
  negative: number
  neutral: number
}

interface TrendChartProps {
  data: TrendDataPoint[]
  periodDays: number
  onPeriodChange: (days: number) => void
  isLoading?: boolean
}

export default function TrendChart({ data, periodDays, onPeriodChange, isLoading }: TrendChartProps) {
  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr)
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
  }

  // T077 - Message données insuffisantes
  const hasEnoughData = data.filter((d) => d.total > 0).length >= 3

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base font-medium">Tendances des mentions</CardTitle>
        {/* T076 - Toggle période 7j/30j */}
        <div className="flex gap-1">
          {[7, 14, 30].map((days) => (
            <Button
              key={days}
              variant={periodDays === days ? 'default' : 'outline'}
              size="sm"
              onClick={() => onPeriodChange(days)}
              className="h-7 px-2 text-xs"
            >
              {days}j
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex h-[300px] items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : !hasEnoughData ? (
          <div className="flex h-[300px] flex-col items-center justify-center text-muted-foreground">
            <p className="text-sm font-medium">Données insuffisantes</p>
            <p className="mt-1 text-xs">
              Au moins 3 jours de données sont nécessaires pour afficher les tendances
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPositive" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorNegative" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorNeutral" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a1a1aa" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#a1a1aa" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                tick={{ fontSize: 11 }}
                className="text-muted-foreground"
              />
              <YAxis tick={{ fontSize: 11 }} className="text-muted-foreground" />
              <Tooltip
                labelFormatter={formatDate}
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                  fontSize: '12px',
                }}
              />
              <Legend iconSize={10} wrapperStyle={{ fontSize: '12px' }} />
              <Area
                type="monotone"
                dataKey="positive"
                name="Positives"
                stroke="#22c55e"
                fill="url(#colorPositive)"
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="neutral"
                name="Neutres"
                stroke="#a1a1aa"
                fill="url(#colorNeutral)"
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="negative"
                name="Négatives"
                stroke="#ef4444"
                fill="url(#colorNegative)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
