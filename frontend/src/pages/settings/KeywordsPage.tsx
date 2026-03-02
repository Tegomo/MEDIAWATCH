import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, Search } from 'lucide-react'
import KeywordForm from '@/components/keywords/KeywordForm'
import KeywordList from '@/components/keywords/KeywordList'
import api from '@/services/api'

interface Keyword {
  id: string
  text: string
  normalized_text: string
  category: string
  enabled: boolean
  alert_enabled: boolean
  alert_threshold: number
  organization_id: string
  total_mentions_count: number
  last_mention_at: string | null
  created_at: string
  updated_at: string
}

interface KeywordListResponse {
  keywords: Keyword[]
  total: number
  limit: number
  offset: number
}

export default function KeywordsPage() {
  const [keywords, setKeywords] = useState<Keyword[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // TODO: Récupérer depuis le profil utilisateur
  const keywordLimit = 10

  const fetchKeywords = useCallback(async () => {
    try {
      const response = await api.get<KeywordListResponse>('/keywords')
      setKeywords(response.data.keywords)
      setTotal(response.data.total)
      setError(null)
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Erreur lors du chargement des mots-clés')
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchKeywords()
  }, [fetchKeywords])

  const handleCreate = async (data: { text: string; category: string }) => {
    try {
      await api.post('/keywords', data)
      await fetchKeywords()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      throw new Error(axiosErr.response?.data?.detail || 'Erreur lors de la création')
    }
  }

  const handleUpdate = async (id: string, data: { text?: string; enabled?: boolean }) => {
    try {
      await api.patch(`/keywords/${id}`, data)
      await fetchKeywords()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'Erreur lors de la mise à jour')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/keywords/${id}`)
      await fetchKeywords()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'Erreur lors de la suppression')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Mots-clés</h1>
          <p className="text-muted-foreground">
            Configurez les mots-clés à surveiller dans les médias ivoiriens
          </p>
        </div>
        <Badge variant="secondary" className="gap-1 text-sm">
          <Search className="h-3 w-3" />
          {total}/{keywordLimit} mots-clés
        </Badge>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}

      {/* Add Keyword Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Ajouter un mot-clé</CardTitle>
          <CardDescription>
            Ajoutez des mots-clés pour surveiller les mentions dans les médias
          </CardDescription>
        </CardHeader>
        <CardContent>
          <KeywordForm
            onSubmit={handleCreate}
            existingKeywords={keywords.map((kw) => kw.text)}
            keywordLimit={keywordLimit}
            currentCount={total}
          />
        </CardContent>
      </Card>

      {/* Keywords List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Vos mots-clés ({total})</CardTitle>
          <CardDescription>
            Gérez vos mots-clés de surveillance. Activez ou désactivez-les selon vos besoins.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <KeywordList
            keywords={keywords}
            onDelete={handleDelete}
            onUpdate={handleUpdate}
          />
        </CardContent>
      </Card>
    </div>
  )
}
