import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const FORBIDDEN_CHARS = ['<', '>', '{', '}', '[', ']', '\\', '|']

const keywordSchema = z.object({
  text: z
    .string()
    .min(2, 'Minimum 2 caractères')
    .max(255, 'Maximum 255 caractères')
    .refine(
      (val) => !FORBIDDEN_CHARS.some((c) => val.includes(c)),
      'Caractères interdits: < > { } [ ] \\ |'
    ),
  category: z.enum(['BRAND', 'PERSON', 'TOPIC', 'ORGANIZATION', 'CUSTOM']),
})

type KeywordFormData = z.infer<typeof keywordSchema>

interface KeywordFormProps {
  onSubmit: (data: { text: string; category: string }) => Promise<void>
  existingKeywords: string[]
  keywordLimit: number
  currentCount: number
}

const categories = [
  { value: 'BRAND', label: 'Marque' },
  { value: 'PERSON', label: 'Personne' },
  { value: 'TOPIC', label: 'Sujet' },
  { value: 'ORGANIZATION', label: 'Organisation' },
  { value: 'CUSTOM', label: 'Personnalisé' },
]

export default function KeywordForm({ onSubmit, existingKeywords, keywordLimit, currentCount }: KeywordFormProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const isLimitReached = currentCount >= keywordLimit

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<KeywordFormData>({
    resolver: zodResolver(keywordSchema),
    defaultValues: {
      category: 'CUSTOM',
    },
  })

  const handleFormSubmit = async (data: KeywordFormData) => {
    setError(null)

    // Vérifier les doublons côté client
    const normalizedNew = data.text.toLowerCase().trim()
    const isDuplicate = existingKeywords.some(
      (kw) => kw.toLowerCase().trim() === normalizedNew
    )
    if (isDuplicate) {
      setError('Ce mot-clé existe déjà')
      return
    }

    if (isLimitReached) {
      setError(`Limite de ${keywordLimit} mots-clés atteinte. Veuillez upgrader votre plan.`)
      return
    }

    setIsLoading(true)
    try {
      await onSubmit({ text: data.text.trim(), category: data.category })
      reset()
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Erreur lors de l\'ajout du mot-clé')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div className="flex gap-3">
        <div className="flex-1 space-y-1">
          <Label htmlFor="keyword-text" className="sr-only">Mot-clé</Label>
          <Input
            id="keyword-text"
            placeholder="Ajouter un mot-clé..."
            disabled={isLimitReached}
            {...register('text')}
          />
          {errors.text && (
            <p className="text-xs text-destructive">{errors.text.message}</p>
          )}
        </div>

        <div className="w-40 space-y-1">
          <Label htmlFor="keyword-category" className="sr-only">Catégorie</Label>
          <select
            id="keyword-category"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            disabled={isLimitReached}
            {...register('category')}
          >
            {categories.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
        </div>

        <Button type="submit" disabled={isLoading || isLimitReached} className="gap-2">
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Ajouter
        </Button>
      </div>

      {error && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}

      {isLimitReached && (
        <div className="rounded-md bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-800">
          Limite de {keywordLimit} mots-clés atteinte.{' '}
          <button className="font-medium underline hover:no-underline">
            Upgrader votre plan
          </button>{' '}
          pour ajouter plus de mots-clés.
        </div>
      )}

      <div className="text-xs text-muted-foreground">
        {currentCount}/{keywordLimit} mots-clés utilisés
      </div>
    </form>
  )
}
