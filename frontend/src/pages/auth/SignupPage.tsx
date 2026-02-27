import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import PaymentForm from '@/components/payments/PaymentForm'
import api from '@/services/api'
import { useTheme } from '@/lib/useTheme'

const signupSchema = z.object({
  email: z.string().email('Email invalide'),
  full_name: z.string().min(2, 'Nom complet requis (min 2 caractères)'),
  organization_name: z.string().min(2, 'Nom d\'organisation requis (min 2 caractères)'),
  password: z
    .string()
    .min(8, 'Minimum 8 caractères')
    .regex(/[A-Z]/, 'Au moins une majuscule')
    .regex(/[a-z]/, 'Au moins une minuscule')
    .regex(/[0-9]/, 'Au moins un chiffre'),
  confirm_password: z.string(),
  subscription_plan: z.enum(['basic', 'pro', 'enterprise']),
}).refine((data) => data.password === data.confirm_password, {
  message: 'Les mots de passe ne correspondent pas',
  path: ['confirm_password'],
})

type SignupFormData = z.infer<typeof signupSchema>

const plans = [
  {
    id: 'basic' as const,
    name: 'Basic',
    price: '25',
    keywords: 10,
    users: 1,
    features: ['10 mots-clés', '1 utilisateur', 'Dashboard basique', 'Alertes email'],
  },
  {
    id: 'pro' as const,
    name: 'Pro',
    price: '99',
    keywords: 50,
    users: 5,
    features: ['50 mots-clés', '5 utilisateurs', 'Analytics avancés', 'Export PDF/Excel', 'Alertes temps réel'],
  },
  {
    id: 'enterprise' as const,
    name: 'Enterprise',
    price: '299',
    keywords: 999,
    users: 999,
    features: ['Mots-clés illimités', 'Utilisateurs illimités', 'API complète', 'Support prioritaire', 'SLA garanti'],
  },
]

export default function SignupPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<'info' | 'plan' | 'payment'>('info')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { theme, toggleTheme } = useTheme()

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      subscription_plan: 'basic',
    },
  })

  const selectedPlan = watch('subscription_plan')

  const onSubmit = async (data: SignupFormData) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await api.post('/auth/signup', {
        email: data.email,
        full_name: data.full_name,
        organization_name: data.organization_name,
        password: data.password,
        subscription_plan: data.subscription_plan,
      })

      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token)
        navigate('/keywords')
      }
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Erreur lors de l\'inscription'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background p-4">
      <button
        onClick={toggleTheme}
        className="absolute right-4 top-4 rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        title={theme === 'dark' ? 'Mode clair' : 'Mode sombre'}
      >
        {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
      </button>
      <div className="w-full max-w-4xl">
        {/* Logo */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-primary">MediaWatch CI</h1>
          <p className="mt-2 text-muted-foreground">Veille médiatique automatisée pour la Côte d'Ivoire</p>
        </div>

        {/* Steps indicator */}
        <div className="mb-8 flex justify-center gap-4">
          {['Informations', 'Plan', 'Paiement'].map((label, i) => {
            const stepKeys = ['info', 'plan', 'payment'] as const
            const isActive = step === stepKeys[i]
            const isPast = stepKeys.indexOf(step) > i
            return (
              <div key={label} className="flex items-center gap-2">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : isPast
                        ? 'bg-green-500 text-white'
                        : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {isPast ? '✓' : i + 1}
                </div>
                <span className={`text-sm ${isActive ? 'font-medium' : 'text-muted-foreground'}`}>
                  {label}
                </span>
              </div>
            )
          })}
        </div>

        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Step 1: Informations */}
          {step === 'info' && (
            <Card className="mx-auto max-w-md">
              <CardHeader>
                <CardTitle>Créer votre compte</CardTitle>
                <CardDescription>Renseignez vos informations pour commencer</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Nom complet</Label>
                  <Input id="full_name" placeholder="Jean Dupont" {...register('full_name')} />
                  {errors.full_name && (
                    <p className="text-sm text-destructive">{errors.full_name.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" placeholder="jean@exemple.ci" {...register('email')} />
                  {errors.email && (
                    <p className="text-sm text-destructive">{errors.email.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="organization_name">Nom de l'organisation</Label>
                  <Input id="organization_name" placeholder="Mon Entreprise" {...register('organization_name')} />
                  {errors.organization_name && (
                    <p className="text-sm text-destructive">{errors.organization_name.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Mot de passe</Label>
                  <Input id="password" type="password" placeholder="Min. 8 caractères" {...register('password')} />
                  {errors.password && (
                    <p className="text-sm text-destructive">{errors.password.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm_password">Confirmer le mot de passe</Label>
                  <Input id="confirm_password" type="password" {...register('confirm_password')} />
                  {errors.confirm_password && (
                    <p className="text-sm text-destructive">{errors.confirm_password.message}</p>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex flex-col gap-4">
                <Button type="button" className="w-full" onClick={() => setStep('plan')}>
                  Continuer
                </Button>
                <p className="text-sm text-muted-foreground">
                  Déjà un compte ?{' '}
                  <Link to="/login" className="text-primary hover:underline">
                    Se connecter
                  </Link>
                </p>
              </CardFooter>
            </Card>
          )}

          {/* Step 2: Plan Selection */}
          {step === 'plan' && (
            <div>
              <div className="grid gap-6 md:grid-cols-3">
                {plans.map((plan) => (
                  <Card
                    key={plan.id}
                    className={`cursor-pointer transition-all hover:shadow-lg ${
                      selectedPlan === plan.id ? 'border-2 border-primary ring-2 ring-primary/20' : ''
                    }`}
                    onClick={() => setValue('subscription_plan', plan.id)}
                  >
                    <CardHeader>
                      <CardTitle>{plan.name}</CardTitle>
                      <CardDescription>
                        <span className="text-3xl font-bold text-foreground">{plan.price}€</span>
                        <span className="text-muted-foreground">/mois</span>
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {plan.features.map((feature) => (
                          <li key={feature} className="flex items-center gap-2 text-sm">
                            <span className="text-green-500">✓</span>
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                ))}
              </div>
              <div className="mt-6 flex justify-center gap-4">
                <Button type="button" variant="outline" onClick={() => setStep('info')}>
                  Retour
                </Button>
                <Button type="button" onClick={() => setStep('payment')}>
                  Continuer avec {plans.find((p) => p.id === selectedPlan)?.name}
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Payment */}
          {step === 'payment' && (
            <Card className="mx-auto max-w-md">
              <CardHeader>
                <CardTitle>Paiement</CardTitle>
                <CardDescription>
                  Plan {plans.find((p) => p.id === selectedPlan)?.name} -{' '}
                  {plans.find((p) => p.id === selectedPlan)?.price}€/mois
                </CardDescription>
              </CardHeader>
              <CardContent>
                <PaymentForm />
                {error && (
                  <div className="mt-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                    {error}
                  </div>
                )}
              </CardContent>
              <CardFooter className="flex flex-col gap-4">
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isLoading ? 'Création du compte...' : 'Créer mon compte'}
                </Button>
                <Button type="button" variant="outline" className="w-full" onClick={() => setStep('plan')}>
                  Retour
                </Button>
              </CardFooter>
            </Card>
          )}
        </form>
      </div>
    </div>
  )
}
