import { useState } from 'react'
import { Trash2, Edit2, Check, X, ToggleLeft, ToggleRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'

interface Keyword {
  id: string
  text: string
  normalized_text: string
  category: string
  enabled: boolean
  alert_enabled: boolean
  alert_threshold: number
  total_mentions_count: number
  created_at: string
}

interface KeywordListProps {
  keywords: Keyword[]
  onDelete: (id: string) => Promise<void>
  onUpdate: (id: string, data: { text?: string; enabled?: boolean }) => Promise<void>
}

const categoryLabels: Record<string, string> = {
  BRAND: 'Marque',
  PERSON: 'Personne',
  TOPIC: 'Sujet',
  ORGANIZATION: 'Organisation',
  CUSTOM: 'Personnalisé',
}

const categoryColors: Record<string, 'default' | 'secondary' | 'outline' | 'success' | 'warning'> = {
  BRAND: 'default',
  PERSON: 'success',
  TOPIC: 'secondary',
  ORGANIZATION: 'warning',
  CUSTOM: 'outline',
}

export default function KeywordList({ keywords, onDelete, onUpdate }: KeywordListProps) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editText, setEditText] = useState('')
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const startEdit = (keyword: Keyword) => {
    setEditingId(keyword.id)
    setEditText(keyword.text)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditText('')
  }

  const saveEdit = async (id: string) => {
    if (editText.trim().length < 2) return
    await onUpdate(id, { text: editText.trim() })
    setEditingId(null)
    setEditText('')
  }

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    try {
      await onDelete(id)
    } finally {
      setDeletingId(null)
    }
  }

  const toggleEnabled = async (keyword: Keyword) => {
    await onUpdate(keyword.id, { enabled: !keyword.enabled })
  }

  if (keywords.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center">
        <p className="text-lg font-medium text-muted-foreground">Aucun mot-clé configuré</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Ajoutez vos premiers mots-clés pour commencer la veille médiatique
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {keywords.map((keyword) => (
        <div
          key={keyword.id}
          className={`flex items-center gap-3 rounded-lg border p-3 transition-colors ${
            keyword.enabled ? 'bg-background' : 'bg-muted/50 opacity-60'
          }`}
        >
          {/* Toggle */}
          <button
            onClick={() => toggleEnabled(keyword)}
            className="text-muted-foreground hover:text-foreground"
            title={keyword.enabled ? 'Désactiver' : 'Activer'}
          >
            {keyword.enabled ? (
              <ToggleRight className="h-5 w-5 text-green-500" />
            ) : (
              <ToggleLeft className="h-5 w-5" />
            )}
          </button>

          {/* Text */}
          <div className="flex-1">
            {editingId === keyword.id ? (
              <div className="flex items-center gap-2">
                <Input
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="h-8"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') saveEdit(keyword.id)
                    if (e.key === 'Escape') cancelEdit()
                  }}
                />
                <Button size="sm" variant="ghost" onClick={() => saveEdit(keyword.id)}>
                  <Check className="h-4 w-4 text-green-500" />
                </Button>
                <Button size="sm" variant="ghost" onClick={cancelEdit}>
                  <X className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="font-medium">{keyword.text}</span>
                <Badge variant={categoryColors[keyword.category] || 'outline'}>
                  {categoryLabels[keyword.category] || keyword.category}
                </Badge>
              </div>
            )}
          </div>

          {/* Mentions count */}
          <div className="text-sm text-muted-foreground">
            {keyword.total_mentions_count} mention{keyword.total_mentions_count !== 1 ? 's' : ''}
          </div>

          {/* Actions */}
          {editingId !== keyword.id && (
            <div className="flex items-center gap-1">
              <Button size="sm" variant="ghost" onClick={() => startEdit(keyword)}>
                <Edit2 className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleDelete(keyword.id)}
                disabled={deletingId === keyword.id}
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
