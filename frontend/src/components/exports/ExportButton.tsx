import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { FileText, FileSpreadsheet, Loader2, Check } from 'lucide-react'
import api from '@/services/api'

interface ExportFilters {
  sentiment?: string | null
  theme?: string | null
  dateFrom?: string
  dateTo?: string
  search?: string
}

interface ExportButtonProps {
  filters: ExportFilters
}

type ExportStatus = 'idle' | 'loading' | 'success' | 'error'

export default function ExportButton({ filters }: ExportButtonProps) {
  const [csvStatus, setCsvStatus] = useState<ExportStatus>('idle')
  const [pdfStatus, setPdfStatus] = useState<ExportStatus>('idle')
  const [pdfTaskId] = useState<string | null>(null)

  const buildParams = () => {
    const params = new URLSearchParams()
    if (filters.sentiment) params.set('sentiment', filters.sentiment)
    if (filters.theme) params.set('theme', filters.theme)
    if (filters.dateFrom) params.set('date_from', `${filters.dateFrom}T00:00:00`)
    if (filters.dateTo) params.set('date_to', `${filters.dateTo}T23:59:59`)
    if (filters.search) params.set('search', filters.search)
    return params.toString()
  }

  const handleCSVExport = async () => {
    setCsvStatus('loading')
    try {
      const params = buildParams()
      const response = await api.post(`/exports/csv?${params}`, null, {
        responseType: 'blob',
      })

      // Télécharger le fichier
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const disposition = response.headers['content-disposition']
      const filename = disposition
        ? disposition.split('filename=')[1]?.replace(/"/g, '')
        : 'mediawatch_export.csv'
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      setCsvStatus('success')
      setTimeout(() => setCsvStatus('idle'), 3000)
    } catch {
      setCsvStatus('error')
      setTimeout(() => setCsvStatus('idle'), 3000)
    }
  }

  const handlePDFExport = async () => {
    setPdfStatus('loading')
    try {
      const params = buildParams()
      const response = await api.post(`/exports/pdf?${params}`, null, {
        responseType: 'blob',
      })

      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const disposition = response.headers['content-disposition']
      const filename = disposition
        ? disposition.split('filename=')[1]?.replace(/"/g, '')
        : 'mediawatch_rapport.pdf'
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      setPdfStatus('success')
      setTimeout(() => setPdfStatus('idle'), 3000)
    } catch {
      setPdfStatus('error')
      setTimeout(() => setPdfStatus('idle'), 3000)
    }
  }

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={handleCSVExport}
        disabled={csvStatus === 'loading'}
        className="gap-1.5"
      >
        {csvStatus === 'loading' ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : csvStatus === 'success' ? (
          <Check className="h-3.5 w-3.5 text-green-500" />
        ) : (
          <FileSpreadsheet className="h-3.5 w-3.5" />
        )}
        CSV
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={handlePDFExport}
        disabled={pdfStatus === 'loading'}
        className="gap-1.5"
      >
        {pdfStatus === 'loading' ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : pdfStatus === 'success' ? (
          <Check className="h-3.5 w-3.5 text-green-500" />
        ) : (
          <FileText className="h-3.5 w-3.5" />
        )}
        PDF
      </Button>

      {/* T098 - Indicateur progression export async */}
      {pdfTaskId && pdfStatus === 'loading' && (
        <span className="text-xs text-muted-foreground">
          Génération en cours...
        </span>
      )}
    </div>
  )
}
