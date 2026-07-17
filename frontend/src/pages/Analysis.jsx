// Analysis Page - Full Featured with Stock Dropdown
// ==================================================

import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { reportsApi, analysisApi, stockApi, documentsApi, chatApi, API_URL } from '../utils/api'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import Chart from 'react-apexcharts'
import { TrendingUp, Shield, Activity, List, ChevronRight, CheckCircle2, Loader2, Search, Download, Zap, BarChart3, Brain, MessageSquare, Heart, Lightbulb, Clock, Target, TrendingDown, ArrowUpRight, ArrowDownRight, Database, FileText, Sparkles, Moon, Sun, Palette, Star, Info, HelpCircle, Mail } from 'lucide-react'
import Joyride from 'react-joyride'
import PriceChart from '../components/PriceChart'
import ForecastChart from '../components/ForecastChart'
import VideoFeed from '../components/VideoFeed'
import SentimentTrend from '../components/SentimentTrend'
import SocialSentiment from '../components/SocialSentiment'

// Popular stocks for dropdown
const POPULAR_STOCKS = [
  { ticker: 'AAPL', name: 'Apple Inc.' },
  { ticker: 'GOOGL', name: 'Alphabet Inc.' },
  { ticker: 'MSFT', name: 'Microsoft Corp.' },
  { ticker: 'AMZN', name: 'Amazon.com Inc.' },
  { ticker: 'TSLA', name: 'Tesla Inc.' },
  { ticker: 'META', name: 'Meta Platforms' },
  { ticker: 'NVDA', name: 'NVIDIA Corp.' },
  { ticker: 'RELIANCE.NS', name: 'Reliance Industries' },
  { ticker: 'TCS.NS', name: 'Tata Consultancy Services' },
  { ticker: 'INFY.NS', name: 'Infosys Ltd.' },
  { ticker: 'HDFCBANK.NS', name: 'HDFC Bank' },
  { ticker: 'ICICIBANK.NS', name: 'ICICI Bank' },
  { ticker: 'WIPRO.NS', name: 'Wipro Ltd.' },
  { ticker: 'ITC.NS', name: 'ITC Ltd.' },
  { ticker: 'SBIN.NS', name: 'State Bank of India' },
]

export default function Analysis() {
  const [ticker, setTicker] = useState('')
  const [stockData, setStockData] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [loadingStock, setLoadingStock] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [loadingReport, setLoadingReport] = useState(false) // For restoring reports

  const navigate = useNavigate()
  const location = useLocation()
  const [activeTab, setActiveTab] = useState('full')
  const [showDropdown, setShowDropdown] = useState(false)
  const [reportId, setReportId] = useState(null)
  const [documents, setDocuments] = useState([])
  const [selectedDocs, setSelectedDocs] = useState([])
  const [forecastDays, setForecastDays] = useState(30)
  const [isWatchlisted, setIsWatchlisted] = useState(false)
  const [runTour, setRunTour] = useState(false)
  const [priceHistory, setPriceHistory] = useState([])
  const [chartPeriod, setChartPeriod] = useState('1y')
  const [customQuestions, setCustomQuestions] = useState('')
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [emailAddress, setEmailAddress] = useState('')
  const [emailing, setEmailing] = useState(false)

  // Tour steps for Educational Mode
  const tourSteps = [
    {
      target: '.ticker-form-v2',
      content: 'Start by entering a stock ticker here to fetch real-time intelligence.',
      disableBeacon: true,
    },
    {
      target: '.analysis-tabs',
      content: 'Choose between a deep Research Report or a quick technical snapshot.',
    },
    {
      target: '.health-sentiment-card',
      content: 'The FHI (Financial Health Index) and Sentiment scores provide a high-level pulse of the asset.',
    },
    {
      target: '.recommendation-card',
      content: 'Our neural core provides a final BUY/SELL/HOLD rating based on all processed signals.',
    }
  ]

  useEffect(() => {
    const handleClickOutside = () => setShowDropdown(false)
    window.addEventListener('click', handleClickOutside)
    fetchDocuments()

    // Check if first visit for tour
    if (!localStorage.getItem('violet-tour-completed')) {
      setRunTour(true)
    }

    return () => window.removeEventListener('click', handleClickOutside)
  }, [])

  useEffect(() => {
    if (location.state?.reportId) {
      loadPersistedReport(location.state.reportId)
    }
  }, [location.state])

  const loadPersistedReport = async (reportId) => {
    setLoadingReport(true)
    try {
      const res = await reportsApi.getData(reportId)
      const data = res.data

      // Restore state
      setTicker(data.ticker)
      setAnalysisResult(data)
      // Re-fetch fresh stock data
      fetchStockData(data.ticker)

      toast.success('Historical Analysis Loaded')
    } catch (error) {
      console.error(error)
      toast.error('Failed to load analysis data')
      // Fallback to fresh analysis or just stay on page?
    } finally {
      setLoadingReport(false)
      // Clear location state to avoid reloading on refresh if desired,
      // but keeping it allows refresh to work if we want.
      // navigate(location.pathname, { replace: true, state: {} })
    }
  }

  const fetchStockData = async (symbol) => {
    if (!symbol) return
    setLoadingStock(true)
    try {
      // Parallel fetch: Quote, Info, and Chart History
      const [priceRes, infoRes, historyRes] = await Promise.all([
        stockApi.getData(symbol),
        stockApi.getInfo(symbol),
        stockApi.getHistory(symbol, chartPeriod)
      ])

      setStockData({
        price: priceRes.data,
        info: infoRes.data
      })
      setPriceHistory(historyRes.data?.data || [])

      checkWatchlist(symbol)
      updateRecentSearches(symbol)
    } catch (error) {
      console.error('Failed to fetch stock data:', error)
      toast.error('Failed to load stock data')
    } finally {
      setLoadingStock(false)
    }
  }

  const checkWatchlist = (symbol) => {
    const watchlist = JSON.parse(localStorage.getItem('violet-watchlist') || '[]')
    setIsWatchlisted(watchlist.includes(symbol))
  }

  const toggleWatchlist = () => {
    if (!ticker) return
    const watchlist = JSON.parse(localStorage.getItem('violet-watchlist') || '[]')
    let newWatchlist
    if (isWatchlisted) {
      newWatchlist = watchlist.filter(t => t !== ticker)
      toast.success(`${ticker} removed from watchlist`)
    } else {
      newWatchlist = Array.from(new Set([...watchlist, ticker]))
      toast.success(`${ticker} added to watchlist`)
    }
    localStorage.setItem('violet-watchlist', JSON.stringify(newWatchlist))
    setIsWatchlisted(!isWatchlisted)
    window.dispatchEvent(new Event('storage'))
  }

  const updateRecentSearches = (symbol) => {
    const recents = JSON.parse(localStorage.getItem('violet-recents') || '[]')
    const filtered = recents.filter(t => t !== symbol)
    const newRecents = [symbol, ...filtered].slice(0, 8)
    localStorage.setItem('violet-recents', JSON.stringify(newRecents))
    window.dispatchEvent(new Event('storage'))
  }

  const fetchDocuments = async () => {
    try {
      const res = await documentsApi.list()
      setDocuments(Array.isArray(res.data) ? res.data : (res.data.documents || []))
    } catch (error) {
      console.error('Failed to fetch documents:', error)
    }
  }

  const parseReportBody = (text) => {
    if (!text) return []

    // Clean generic artifacts
    let cleanText = text.trim()
    if (cleanText.startsWith('"') && cleanText.endsWith('"')) {
      cleanText = cleanText.slice(1, -1)
    }

    const sections = []

    // Pre-process: Handle standard Markdown headers
    const lines = []

    // First, normalize line endings and split
    const normalizedText = cleanText.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
    const splitLines = normalizedText.split('\n')

    splitLines.forEach(rawLine => {
      const trimmed = rawLine.trim()
      if (!trimmed) return
      if (trimmed === '"' || trimmed === '.') return

      lines.push(trimmed)
    })

    // Helper to identify header lines
    const isHeader = (line) => {
      // Standard Markdown Header (e.g. # Title, ## Title, ### Title)
      if (line.match(/^#{1,6}\s+/)) return true

      // Bold Headers (e.g. **Title**) - often used by LMs
      if (line.match(/^\*\*.+\*\*[:\s]*$/)) return true

      // Numbered Bold Headers (e.g. 1. **Title**)
      if (line.match(/^\d+\.\s+\*\*.+\*\*[:\s]*$/)) return true

      return false
    }

    // Extract clean title from header line
    const extractTitle = (line) => {
      return line
        .replace(/^#{1,6}\s+/, '')      // Remove ### 
        .replace(/^\d+\.\s+/, '')       // Remove 1. 
        .replace(/^\*\*/, '')           // Remove leading **
        .replace(/\*\*[:\s]*$/, '')     // Remove trailing **:
        .replace(/:$/, '')              // Remove trailing :
        .trim()
    }

    // Map titles to specific interactive modules
    const getTypeFromTitle = (title) => {
      const lowerTitle = title.toLowerCase()

      // Radar Chart Module (Key Metrics)
      if (
        lowerTitle.includes('metric') ||
        lowerTitle.includes('indicator') ||
        lowerTitle.includes('kpi') ||
        lowerTitle.includes('technical outlook')
      ) {
        return 'radar'
      }

      // Signals Module (Risk, Health, Strengths)
      else if (
        lowerTitle.includes('signal') ||
        lowerTitle.includes('risk') ||
        lowerTitle.includes('health') ||
        lowerTitle.includes('strength') ||
        lowerTitle.includes('swot') ||
        lowerTitle.includes('financial health')
      ) {
        return 'signals'
      }

      // Actions Module (Strategy, Steps)
      else if (
        lowerTitle.includes('action') ||
        lowerTitle.includes('plan') ||
        lowerTitle.includes('recommendation') ||
        lowerTitle.includes('investment case')
      ) {
        return 'actions'
      }

      // Custom Questions Response
      else if (
        lowerTitle.includes('custom question') ||
        lowerTitle.includes('user question') ||
        lowerTitle.includes('your question')
      ) {
        return 'custom'
      }

      return 'standard'
    }

    let currentSection = null

    lines.forEach(line => {
      // Skip tiny artifacts
      if (line.length < 2) return

      if (isHeader(line)) {
        if (currentSection) sections.push(currentSection)

        const title = extractTitle(line)
        currentSection = {
          title: title,
          content: [],
          id: Math.random().toString(36).substr(2, 9),
          type: getTypeFromTitle(title),
          data: null
        }
      } else {
        if (!currentSection) {
          // First non-header line - create default section
          currentSection = { title: 'Executive Summary', content: [line], id: 'initial', type: 'standard' }
        } else {
          currentSection.content.push(line)
        }
      }
    })

    if (currentSection) sections.push(currentSection)

    // Remove sections with only artifact content
    const filteredSections = sections.filter(s => {
      // For generic "Overview" section, check if it has real content
      if (s.title === 'Overview' || s.title === 'Executive Summary') {
        const realContent = s.content.filter(c => c.length >= 5 && !c.match(/^[.\-"'\s,;:]+$/))
        return realContent.length > 0
      }
      return s.content.length > 0
    })

    // Merge sections with same title
    const mergedSections = []
    filteredSections.forEach(sec => {
      const existing = mergedSections.find(s => s.title.toLowerCase() === sec.title.toLowerCase())
      if (existing) {
        existing.content = [...existing.content, ...sec.content]
      } else {
        mergedSections.push(sec)
      }
    })

    // Data Extraction from content
    return mergedSections.map(sec => {
      if (sec.type === 'radar') {
        // Attempt to extract label: value% pairs
        sec.data = sec.content
          .map(l => l.match(/(.*?):\s*(\d+)%/))
          .filter(m => m)
          .map(m => ({ label: m[1].replace(/[*\-]/g, '').trim(), value: parseInt(m[2]) }))

        // Use fallbacks if no percentage data found
        if (sec.data.length < 1) sec.type = 'standard'
      }
      else if (sec.type === 'signals') {
        // Attempt to extract risk signals or strengths
        let baseValue = 85 // Start at 85% for varied effect
        const extractedSignals = sec.content
          .map(l => {
            // Try to find "Label: Value%" format
            const metric = l.match(/(.*?):\s*(\d+)%/)
            if (metric) return { label: metric[1].replace(/[*\-]/g, '').trim(), value: parseInt(metric[2]) }

            // Try to find "Value% Label" format
            const metricReverse = l.match(/(\d+)%\s*(.+)/)
            if (metricReverse) return { label: metricReverse[2].replace(/[*\-]/g, '').trim(), value: parseInt(metricReverse[1]) }

            // Try to find any percentage in the line
            const anyPercent = l.match(/(\d+)%/)
            if (anyPercent) {
              const cleanLabel = l.replace(/(\d+)%/g, '').replace(/[*\-:]/g, '').trim()
              if (cleanLabel.length > 3 && cleanLabel.length < 60) {
                return { label: cleanLabel, value: parseInt(anyPercent[1]) }
              }
            }

            // Short bullet points - assign varied values (decreasing from 85)
            const bullet = l.match(/^[-*]\s*(.+)$/)
            if (bullet && bullet[1].length < 60 && bullet[1].length > 5) {
              baseValue = Math.max(55, baseValue - 5) // Decrease by 5 each time, min 55%
              return { label: bullet[1].trim(), value: baseValue }
            }

            // Ignore long text bullets
            return null
          })
          .filter(d => d)

        if (extractedSignals.length > 0) {
          sec.data = extractedSignals
        } else {
          sec.type = 'standard' // Fallback to standard text if no valid signals found
        }
      }
      else if (sec.type === 'actions') {
        sec.data = sec.content
          .filter(l => l.match(/^(?:\d+\.|\*|-)/))
          .map(l => l.replace(/^(?:\d+\.|\*|-)/, '').replace(/\*\*/g, '').trim())
      }
      return sec
    })
  }

  // Loading Components
  const LoadingSpinner = ({ size = 20, text = 'Loading...' }) => (
    <div className="loading-spinner-container">
      <Loader2 className="spinner-icon" size={size} />
      {text && <span className="spinner-text">{text}</span>}
    </div>
  )

  const SkeletonCard = () => (
    <div className="skeleton-card">
      <div className="skeleton-line wide" />
      <div className="skeleton-line medium" />
      <div className="skeleton-line narrow" />
    </div>
  )

  // Modular UI Components
  const RadarChartModule = ({ data }) => {
    // Metric explanations for tooltips
    const explanations = {
      'Bullish Momentum': 'Indicates upward price trend strength based on recent price action',
      'RSI Health': 'Relative Strength Index health - measures overbought/oversold conditions',
      'MACD Trend': 'Moving Average Convergence Divergence - signal for trend direction',
      '20Day Moving Average': 'Price position relative to 20-day moving average',
      'Volume Trend': 'Trading volume trend compared to historical average',
      'Support Strength': 'Strength of nearby price support levels',
      'Resistance Proximity': 'Distance to key resistance levels',
    }

    const options = {
      chart: {
        toolbar: { show: false },
        background: 'transparent',
        dropShadow: {
          enabled: true,
          blur: 3,
          color: '#7c3aed',
          opacity: 0.3
        }
      },
      colors: ['#a855f7'],
      xaxis: {
        categories: data.map(d => d.label),
        labels: {
          style: {
            colors: data.map(() => '#e2e8f0'), // Brighter white labels
            fontSize: '11px',
            fontWeight: 600
          },
          offsetY: 5 // More spacing from chart
        }
      },
      yaxis: { show: false, min: 0, max: 100 },
      stroke: { width: 2, colors: ['#a855f7'] },
      fill: {
        opacity: 0.4,
        colors: ['#7c3aed'],
        type: 'gradient',
        gradient: {
          shade: 'dark',
          shadeIntensity: 0.5,
          gradientToColors: ['#c084fc'],
          opacityFrom: 0.5,
          opacityTo: 0.2,
        }
      },
      markers: {
        size: 5,
        colors: ['#a855f7'],
        strokeColors: '#fff',
        strokeWidth: 2,
        hover: { size: 8 }
      },
      tooltip: {
        theme: 'dark',
        style: { fontSize: '12px' },
        custom: function ({ dataPointIndex }) {
          const item = data[dataPointIndex]
          const explanation = explanations[item.label] || 'Technical indicator score'
          return `
            <div style="background: #1e1b4b; border: 1px solid #7c3aed; border-radius: 8px; padding: 12px; min-width: 200px;">
              <div style="color: #a855f7; font-weight: 700; font-size: 14px; margin-bottom: 6px;">${item.label}</div>
              <div style="color: #10b981; font-size: 20px; font-weight: 700; margin-bottom: 8px;">● Score: ${item.value}%</div>
              <div style="color: #cbd5e1; font-size: 11px; line-height: 1.4;">${explanation}</div>
            </div>
          `
        }
      },
      plotOptions: {
        radar: {
          size: 100,
          polygons: {
            strokeColors: 'rgba(124, 58, 237, 0.2)',
            strokeWidth: 1,
            connectorColors: 'rgba(124, 58, 237, 0.15)',
            fill: { colors: ['rgba(0,0,0,0.1)', 'rgba(0,0,0,0.05)'] }
          }
        }
      }
    }
    return (
      <div className="radar-module">
        <Chart options={options} series={[{ name: 'Score', data: data.map(d => d.value) }]} type="radar" height={280} />
        <div className="radar-legend">
          {data.map((item, i) => (
            <div key={i} className="radar-legend-item" title={explanations[item.label] || ''}>
              <span className="legend-dot" style={{ background: item.value > 70 ? '#10b981' : item.value > 40 ? '#f59e0b' : '#ef4444' }}></span>
              <span className="legend-label">{item.label}</span>
              <span className="legend-value">{item.value}%</span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const SignalsModule = ({ data }) => (
    <div className="signals-grid">
      {data.map((sig, i) => (
        <div key={i} className="signal-item">
          <div className="signal-meta">
            <span className="signal-label">{sig.label}</span>
            <span className="signal-value">{sig.value}%</span>
          </div>
          <div className="signal-bar-bg">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${sig.value}%` }}
              className="signal-bar-fill"
              style={{ background: sig.value > 70 ? '#10b981' : sig.value > 40 ? '#f59e0b' : '#ef4444' }}
            />
          </div>
        </div>
      ))}
    </div>
  )

  const ActionsModule = ({ data }) => (
    <div className="actions-stepper">
      {data.map((step, i) => (
        <div key={i} className="step-item">
          <div className="step-line-wrapper">
            <div className="step-dot"><CheckCircle2 size={14} /></div>
            {i < data.length - 1 && <div className="step-line" />}
          </div>
          <div className="step-content">
            <span className="step-badge">Step {i + 1}</span>
            <p>{step}</p>
          </div>
        </div>
      ))}
    </div>
  )

  const toggleDocSelection = (docId) => {
    setSelectedDocs(prev =>
      prev.includes(docId)
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    )
  }

  const handleSelectStock = (selectedTicker) => {
    setTicker(selectedTicker)
    setShowDropdown(false)
    // Auto-fetch after selection
    handleFetchStockByTicker(selectedTicker)
  }

  const handleFetchStockByTicker = async (tickerValue) => {
    if (!tickerValue.trim()) return

    // Clear previous state before fetching new
    setAnalysisResult(null)
    setReportId(null)
    setStockData(null)

    // fetchStockData handles loading state, history fetching, and error handling
    await fetchStockData(tickerValue.toUpperCase())
  }

  const handleFetchStock = async (e) => {
    e.preventDefault()
    handleFetchStockByTicker(ticker)
  }

  const handleRunAnalysis = async () => {
    if (!ticker) return

    setAnalyzing(true)

    try {
      const res = await analysisApi.start({
        ticker: ticker.toUpperCase(),
        include_forecast: true,
        include_sentiment: true,
        include_recommendation: true,
        document_ids: selectedDocs,
        forecast_days: forecastDays,
        custom_questions: customQuestions || null
      })

      const jobId = res.data.job_id
      toast.success('Analysis started! Using ' + (selectedDocs.length > 0 ? selectedDocs.length : 'no') + ' RAG documents.')

      // Poll for results
      const pollResult = async () => {
        const result = await analysisApi.getResult(jobId)

        if (result.data.status === 'completed') {
          setAnalysisResult(result.data.result)
          if (result.data.result.report_path) {
            // Extract report ID from path (handle / and \)
            const path = result.data.result.report_path;
            const filename = path.split(/[/\\]/).pop();
            const reportName = filename.replace('.pdf', '');
            setReportId(reportName);
          }
          toast.success('Analysis complete!')
          setAnalyzing(false)
        } else if (result.data.status === 'failed') {
          toast.error('Analysis failed: ' + result.data.error)
          setAnalyzing(false)
        } else {
          setTimeout(pollResult, 3000)
        }
      }

      pollResult()
    } catch (error) {
      toast.error('Failed to start analysis')
      setAnalyzing(false)
    }
  }

  const handleQuickAnalysis = async (type) => {
    if (!ticker) {
      toast.error('Please enter a ticker first')
      return
    }

    setAnalyzing(true)

    try {
      let res
      switch (type) {
        case 'sentiment':
          res = await analysisApi.sentiment({ ticker: ticker.toUpperCase() })
          setAnalysisResult({
            sentiment: res.data.sentiment,
            fhi: res.data.fhi
          })
          break
        case 'forecast':
          res = await analysisApi.forecast({ ticker: ticker.toUpperCase() })
          setAnalysisResult({
            forecast: res.data.forecast
          })
          break
        case 'recommend':
          res = await analysisApi.recommend({ ticker: ticker.toUpperCase() })
          setAnalysisResult({
            recommendation: res.data.recommendation,
            fhi: res.data.fhi,
            sentiment: res.data.sentiment
          })
          break
        case 'fhi':
          res = await analysisApi.fhi({ ticker: ticker.toUpperCase() })
          setAnalysisResult({
            fhi: res.data.fhi
          })
          break
      }
      toast.success(`${type.charAt(0).toUpperCase() + type.slice(1)} analysis complete!`)
    } catch (error) {
      toast.error(`Failed to run ${type} analysis`)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleDownloadReport = async () => {
    if (!reportId) {
      toast.error('No report available to download');
      return;
    }

    try {
      const res = await reportsApi.download(reportId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${ticker}_Research_Report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Report downloaded!');
    } catch (error) {
      console.error(error);
      toast.error('Failed to download report');
    }
  };

  const handleEmailReport = async (e) => {
    e.preventDefault();
    if (!reportId || !emailAddress) return;

    setEmailing(true);
    try {
      await reportsApi.emailReport(reportId, emailAddress);
      toast.success(`Report sent to ${emailAddress}`);
      setShowEmailModal(false);
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || 'Failed to send email report');
    } finally {
      setEmailing(false);
    }
  };

  const handleExportCSV = () => {
    if (!analysisResult) {
      toast.error('No analysis result to export')
      return
    }

    let csv = 'Metric,Value,Confidence/Note\n'
    csv += `Ticker,${ticker},Official Search Symbol\n`
    csv += `Company Name,${stockData?.info?.longName || ticker},Verified Legal Entity\n`
    csv += `Price,${stockData?.price?.current_price || 'N/A'},Last Trade Price\n`

    if (analysisResult.fhi) {
      csv += `FHI Score,${analysisResult.fhi.score || 'N/A'},Financial Health Index (0-100)\n`
      csv += `FHI Grade,${analysisResult.fhi.grade || 'N/A'},Health Classification\n`
    }

    if (analysisResult.sentiment) {
      csv += `Sentiment,${analysisResult.sentiment.label || 'N/A'},Overall Market Mood\n`
      csv += `Sentiment Score,${analysisResult.sentiment.compound || 'N/A'},Neural Tone Aggregator\n`
    }

    if (analysisResult.recommendation) {
      csv += `Final Rating,${analysisResult.recommendation.rating || 'N/A'},AI Neural Conclusion\n`
      csv += `Confidence,${((analysisResult.recommendation.confidence || 0) * 100).toFixed(0)}%,Engine Reliability Factor\n`
    }

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `VioletAI_${ticker}_Analysis.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    toast.success('Intelligence exported to CSV')
  }


  const getRatingColor = (rating) => {
    switch (rating?.toUpperCase()) {
      case 'BUY':
      case 'STRONG BUY':
        return 'var(--accent-success)'
      case 'SELL':
      case 'STRONG SELL':
        return 'var(--accent-danger)'
      default:
        return 'var(--accent-warning)'
    }
  }

  const filteredStocks = POPULAR_STOCKS.filter(
    stock =>
      stock.ticker.toLowerCase().includes(ticker.toLowerCase()) ||
      stock.name.toLowerCase().includes(ticker.toLowerCase())
  )

  return (
    <div className="analysis-page">
      <Joyride
        run={runTour}
        steps={tourSteps}
        continuous
        showProgress
        showSkipButton
        callback={(data) => {
          if (['finished', 'skipped'].includes(data.status)) {
            localStorage.setItem('violet-tour-completed', 'true');
            setRunTour(false);
          }
        }}
        styles={{
          options: {
            primaryColor: 'var(--accent-primary)',
            textColor: 'var(--text-main)',
            backgroundColor: 'var(--bg-dark-800)',
          }
        }}
      />
      <header className="page-header">
        <div className="header-main">
          <h1><Zap size={28} className="header-icon" /> Stock Analysis</h1>
          <p>AI-powered equity research with forecasting, sentiment analysis & recommendations</p>
        </div>
      </header>

      {!analysisResult && (
        <div className="search-container">
          <form className="ticker-form-v2" onSubmit={handleFetchStock}>
            <div
              className="ticker-input-wrapper"
              onClick={(e) => e.stopPropagation()}
            >
              <input
                type="text"
                className="ticker-input"
                placeholder="Enter ticker or search stocks..."
                value={ticker}
                onChange={(e) => {
                  setTicker(e.target.value.toUpperCase())
                  setShowDropdown(true)
                }}
                onFocus={(e) => {
                  e.stopPropagation()
                  setShowDropdown(true)
                }}
                autoComplete="off"
              />
              {showDropdown && (
                <div className="stock-dropdown-v2 glass-card">
                  {(ticker ? filteredStocks : POPULAR_STOCKS).map((stock) => (
                    <div
                      key={stock.ticker}
                      className="dropdown-item-v2"
                      onClick={() => handleSelectStock(stock.ticker)}
                    >
                      <div className="stock-main-info">
                        <span className="stock-symbol-v2">{stock.ticker}</span>
                        <span className="stock-name-v2">{stock.name}</span>
                      </div>
                      <span className="stock-type-v2">Equity</span>
                    </div>
                  ))}
                  {(ticker ? filteredStocks : POPULAR_STOCKS).length === 0 && (
                    <div className="dropdown-item-v2 empty">No stocks found</div>
                  )}
                </div>
              )}
            </div>

            <button type="submit" className="btn-fetch-v2" disabled={loadingStock}>
              {loadingStock ? (
                <Loader2 className="spinner-icon" size={18} />
              ) : (
                <><Search size={16} /> <span className="btn-text">Fetch Stock</span></>
              )}
            </button>
          </form>

          <div className="popular-tags">
            <span className="tags-label">Quick Intel:</span>
            <div className="tags-group">
              {['AAPL', 'RELIANCE.NS', 'TCS.NS', 'GOOGL', 'MSFT', 'NVDA', 'TSLA'].map(t => (
                <button
                  key={t}
                  className="tag-chip"
                  onClick={() => handleSelectStock(t)}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {stockData && (
        <div className="stock-data">
          <div className="stock-header">
            <div className="header-title-row">
              <h2>{stockData.info.name || ticker}</h2>
              <button
                className={`star-btn ${isWatchlisted ? 'active' : ''}`}
                onClick={toggleWatchlist}
                title={isWatchlisted ? "Remove from Watchlist" : "Add to Watchlist"}
              >
                <Star size={20} fill={isWatchlisted ? "var(--accent-primary)" : "none"} />
              </button>
            </div>
            <div className="header-meta-row">
              <span className="sector">{stockData.info.sector}</span>
              {stockData.info.industry && (
                <span className="industry">{stockData.info.industry}</span>
              )}
            </div>
          </div>

          <div className="price-info">
            <div className="current-price">
              <span className="currency">{ticker.endsWith('.NS') || ticker.endsWith('.BO') ? '₹' : '$'}</span>
              <span className="price">{stockData.price.current_price?.toFixed(2) || 'N/A'}</span>
              <span className={`change ${stockData.price.change >= 0 ? 'positive' : 'negative'}`}>
                {stockData.price.change >= 0 ? '+' : ''}{stockData.price.change?.toFixed(2) || 0}
                ({stockData.price.change_percent?.toFixed(2) || 0}%)
              </span>
            </div>

            <div className="price-details">
              <div className="detail">
                <span className="label">Open</span>
                <span className="value">{stockData.price.open?.toFixed(2) || 'N/A'}</span>
              </div>
              <div className="detail">
                <span className="label">High</span>
                <span className="value">{stockData.price.day_high?.toFixed(2) || 'N/A'}</span>
              </div>
              <div className="detail">
                <span className="label">Low</span>
                <span className="value">{stockData.price.day_low?.toFixed(2) || 'N/A'}</span>
              </div>
              <div className="detail">
                <span className="label">Volume</span>
                <span className="value">{stockData.price.volume ? (stockData.price.volume / 1000000).toFixed(2) + 'M' : 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Interactive Price Chart */}
          <PriceChart data={priceHistory} ticker={ticker} period={chartPeriod} />

          <div className="analysis-tabs">
            <button
              className={`tab ${activeTab === 'full' ? 'active' : ''}`}
              onClick={() => setActiveTab('full')}
            >
              <Sparkles size={16} /> Full Analysis
            </button>
            <button
              className={`tab ${activeTab === 'quick' ? 'active' : ''}`}
              onClick={() => setActiveTab('quick')}
            >
              <Zap size={16} /> Quick Analysis
            </button>
          </div>

          {!analysisResult && (
            activeTab === 'full' ? (
              <div className="full-analysis-controls">
                {documents.length > 0 && (
                  <div className="document-selection">
                    <h3> Include Documents for RAG (Optional)</h3>
                    <p className="selection-hint">Select documents to enhance AI insights with your own research</p>
                    <div className="docs-grid">
                      {documents.map(doc => (
                        <label key={doc.id} className={`doc-item ${selectedDocs.includes(doc.id) ? 'selected' : ''}`}>
                          <input
                            type="checkbox"
                            checked={selectedDocs.includes(doc.id)}
                            onChange={() => toggleDocSelection(doc.id)}
                          />
                          <span className="doc-name">{doc.filename}</span>
                          <span className="doc-type">{doc.file_type}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                <div className="forecast-params">
                  <label><Clock size={16} className="icon-accent" /> Forecast Period: <strong>{forecastDays} Days</strong></label>
                  <div className="forecast-options">
                    {[7, 14, 30, 60, 90].map(days => (
                      <button
                        key={days}
                        className={`option-btn ${forecastDays === days ? 'active' : ''}`}
                        onClick={() => setForecastDays(days)}
                      >
                        {days}d
                      </button>
                    ))}
                  </div>
                </div>

                <div className="custom-questions-section">
                  <label><HelpCircle size={16} className="icon-accent" /> Custom Report Questions (Optional)</label>
                  <p className="selection-hint">What specific questions should the AI address in the report?</p>
                  <textarea
                    className="custom-questions-input"
                    placeholder="E.g., What are the key risks for this stock? How does it compare to competitors? What's the dividend outlook?"
                    value={customQuestions}
                    onChange={(e) => setCustomQuestions(e.target.value)}
                    rows={3}
                  />
                </div>

                <button
                  onClick={handleRunAnalysis}
                  className="btn-analyze"
                  disabled={analyzing}
                >
                  {analyzing ? (
                    <><Loader2 className="spinner-icon" size={18} /> Running Analysis...</>
                  ) : (
                    <><Brain size={18} /> Run Full Analysis</>
                  )}
                </button>
              </div>
            ) : (
              <div className="quick-analysis-buttons">
                <button onClick={() => handleQuickAnalysis('forecast')} disabled={analyzing} className="btn-quick">
                  {analyzing ? <Loader2 className="spinner-icon" size={16} /> : <BarChart3 size={18} />}
                  <span>Forecast</span>
                </button>
                <button onClick={() => handleQuickAnalysis('sentiment')} disabled={analyzing} className="btn-quick">
                  {analyzing ? <Loader2 className="spinner-icon" size={16} /> : <MessageSquare size={18} />}
                  <span>Sentiment</span>
                </button>
                <button onClick={() => handleQuickAnalysis('fhi')} disabled={analyzing} className="btn-quick">
                  {analyzing ? <Loader2 className="spinner-icon" size={16} /> : <Heart size={18} />}
                  <span>FHI Score</span>
                </button>
                <button onClick={() => handleQuickAnalysis('recommend')} disabled={analyzing} className="btn-quick">
                  {analyzing ? <Loader2 className="spinner-icon" size={16} /> : <Lightbulb size={18} />}
                  <span>Recommend</span>
                </button>
              </div>
            )
          )}

          {/* Analysis Loading Overlay */}
          <AnimatePresence>
            {(analyzing || loadingReport) && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="analyzing-overlay"
              >
                <div className="analyzing-content">
                  <div className="analyzing-spinner">
                    <Loader2 className="main-spinner" size={40} />
                  </div>
                  <h3>{analyzing ? `Analyzing ${ticker}...` : `Restoring ${ticker} Analysis...`}</h3>
                  <p>{analyzing ? 'Running AI-powered analysis. This may take a moment.' : 'Retrieving secured intelligence data from vault.'}</p>
                  {analyzing && (
                    <div className="analyzing-steps">
                      <div className="step active"><Database size={14} /> <span>Data</span></div>
                      <div className="step-connector" />
                      <div className="step"><BarChart3 size={14} /> <span>Forecast</span></div>
                      <div className="step-connector" />
                      <div className="step"><MessageSquare size={14} /> <span>Sentiment</span></div>
                      <div className="step-connector" />
                      <div className="step"><FileText size={14} /> <span>Report</span></div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {analysisResult && (
        <div className="analysis-results">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="results-header"
          >
            <h2 className="outfit"><Sparkles className="icon-gold" size={28} /> Analysis Highlights</h2>
            <div className="header-actions">
              <button onClick={handleExportCSV} className="btn-secondary-v2">
                <BarChart3 size={18} /> Export CSV
              </button>
              {reportId && (
                <>
                  <button onClick={() => setShowEmailModal(true)} className="btn-secondary-v2">
                    <Mail size={18} /> Email Report
                  </button>
                  <button onClick={handleDownloadReport} className="btn-primary-v2">
                    <Download size={18} /> Download Report
                  </button>
                </>
              )}
              <button onClick={() => setRunTour(true)} className="btn-icon-v2" title="Tutorial">
                <HelpCircle size={18} />
              </button>
              <button
                onClick={() => setAnalysisResult(null)}
                className="btn-primary-v2"
                style={{ background: 'var(--bg-dark-700)', border: '1px solid var(--glass-border)' }}
              >
                <Zap size={18} /> New Analysis
              </button>
            </div>
          </motion.div>

          <div className="result-cards-grid">
            {/* Recommendation Card */}
            {analysisResult.recommendation && (
              <div className="glass-card recommendation-card">
                <div className="card-header-row">
                  <h3 className="outfit"><Lightbulb className="icon-accent" size={22} /> AI Recommendation</h3>
                  {analysisResult.recommendation.risk_level && (
                    <span className={`risk-badge ${analysisResult.recommendation.risk_level.toLowerCase()}`}>
                      {analysisResult.recommendation.risk_level} Risk
                    </span>
                  )}
                </div>
                <div
                  className="rating-badge"
                  style={{
                    background: getRatingColor(analysisResult.recommendation.rating),
                    boxShadow: `0 0 20px ${getRatingColor(analysisResult.recommendation.rating)}44`
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                    {analysisResult.recommendation.rating === 'BUY' && <TrendingUp size={24} />}
                    {analysisResult.recommendation.rating === 'SELL' && <TrendingDown size={24} />}
                    {analysisResult.recommendation.rating === 'HOLD' && <Activity size={24} />}
                    {analysisResult.recommendation.rating}
                  </span>
                </div>
                <div className="confidence-meter">
                  <div className="meter-label">
                    <span>Confidence</span>
                    <span>{((analysisResult.recommendation.confidence || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="meter-track">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(analysisResult.recommendation.confidence || 0) * 100}%` }}
                      className="meter-fill"
                    />
                  </div>
                </div>
                <div className="risk-level">
                  <Shield size={16} className="text-muted" />
                  <span className="text-muted">Risk Profile:</span>
                  <div className="risk-score-display">
                    <span className="risk-text">{analysisResult.recommendation.risk_level || 'Moderate'}</span>
                    {stockData?.price?.risk_score && (
                      <span className="risk-number">({stockData.price.risk_score}/100)</span>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Health & Sentiment */}
            <div className="glass-card health-sentiment-card">
              <h3 className="outfit"><Activity className="icon-accent" size={22} /> Market Vitals</h3>
              <div className="vitals-grid">
                <div className="vital-item">
                  <span className="vital-label">FHI Score</span>
                  <div className="vital-value-row">
                    <span className="vital-value violet">{analysisResult.fhi?.score || 'N/A'}</span>
                  </div>
                  <span className="vital-sub">Grade: <strong>{analysisResult.fhi?.grade || '-'}</strong></span>
                </div>
                <div className="vital-item">
                  <span className="vital-label">Sentiment</span>
                  <div className="vital-value-row">
                    <span className="vital-value">{analysisResult.sentiment?.compound?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <span className={`vital-sub sentiment-label ${(analysisResult.sentiment?.label || 'Neutral').toLowerCase()}`}>
                    {analysisResult.sentiment?.label || 'Neutral'}
                  </span>
                </div>
              </div>
            </div>

            {/* Forecast Summary */}
            {analysisResult.forecast && (
              <div className="glass-card forecast-summary-card">
                <h3 className="outfit"><TrendingUp className="icon-accent" size={22} /> Price Outlook</h3>
                <div className="outlook-data">
                  <div className="outlook-price">
                    <span className="price-label">Target (30d)</span>
                    <span className="price-value"> ${analysisResult.forecast.target_price?.toFixed(2)}</span>
                  </div>
                  <div className={`outlook-trend ${analysisResult.forecast.trend?.toLowerCase()}`}>
                    {analysisResult.forecast.trend === 'BULLISH' && <TrendingUp size={16} />}
                    {analysisResult.forecast.trend === 'BEARISH' && <TrendingDown size={16} />}
                    {analysisResult.forecast.trend === 'NEUTRAL' && <Activity size={16} />}
                    {analysisResult.forecast.trend}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* NEW: Report Preview Section */}
          {
            analysisResult.report_body && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="report-preview-container"
              >
                <div className="preview-header-v2">
                  <h2 className="outfit"><FileText className="icon-accent" size={28} /> AI Intelligence Briefing</h2>
                  <div className="header-badges">
                    <span className="badge-neural"><Brain size={14} /> Neural Core</span>
                    <span className="badge-premium"><Shield size={14} /> Research Premium</span>
                  </div>
                </div>

                <div className="report-sections-grid">
                  {parseReportBody(analysisResult.report_body).map((section, idx) => (
                    <motion.div
                      key={section.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 * idx }}
                      className={`glass-card report-section-card type-${section.type}`}
                    >
                      <div className="section-card-header">
                        <div className="section-title-group">
                          <span className="section-number">0{idx + 1}</span>
                          <h3 className="outfit">{section.title}</h3>
                        </div>
                        <div className="section-icon">
                          {section.type === 'radar' && <Activity size={18} />}
                          {section.type === 'signals' && <TrendingUp size={18} />}
                          {section.type === 'actions' && <Shield size={18} />}
                          {section.type === 'custom' && <HelpCircle size={18} />}
                        </div>
                      </div>

                      <div className="section-card-content">
                        {section.type === 'radar' && section.data && <RadarChartModule data={section.data} />}
                        {section.type === 'signals' && section.data && <SignalsModule data={section.data} />}
                        {section.type === 'actions' && section.data && <ActionsModule data={section.data} />}

                        {section.content.map((p, pIdx) => {
                          // Don't repeat data lines in standard paragraph if we already rendered them as modules
                          if ((section.type === 'radar' || section.type === 'signals') && p.includes(':')) return null;
                          if (section.type === 'actions' && p.match(/^(?:\d+\.|\*|-)/)) return null;

                          const renderWithBold = (text) => {
                            const parts = text.split(/(\*\*.*?\*\*)/g);
                            return parts.map((part, i) => {
                              if (part.startsWith('**') && part.endsWith('**')) {
                                return <strong key={i} className="report-bold">{part.slice(2, -2)}</strong>;
                              }
                              return part;
                            });
                          };

                          // List Item Rendering
                          if (p.match(/^[\*\-]\s/)) {
                            return (
                              <div key={pIdx} className="report-bullet-row">
                                <span className="bullet-dot">•</span>
                                <span className="bullet-text">{renderWithBold(p.replace(/^[\*\-]\s*/, ''))}</span>
                              </div>
                            )
                          }

                          // Regular Paragraph
                          return <p key={pIdx} className="report-paragraph">{renderWithBold(p)}</p>
                        })}
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Charts Section - Full Width Below Grid */}
                {analysisResult.forecast?.points ? (
                  <ForecastChart data={analysisResult.forecast.points} ticker={analysisResult.ticker} />
                ) : analysisResult.chart_url && (
                  <div className="glass-card full-width-chart" style={{ marginTop: '2rem' }}>
                    <h3 className="outfit"><BarChart3 className="icon-accent" size={22} /> Trend Visualization</h3>
                    <div className="forecast-chart-container">
                      <img
                        src={`${API_URL}${analysisResult.chart_url}`}
                        alt="Forecast Chart"
                        className="forecast-chart-img"
                      />
                    </div>
                  </div>
                )}
              </motion.div>
            )
          }

          <VideoFeed ticker={ticker} />
          <SentimentTrend ticker={ticker} />
          <SocialSentiment ticker={ticker} />
        </div >
      )
      }

      {/* Email Report Modal */}
      <AnimatePresence>
        {showEmailModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="modal-overlay"
            onClick={() => setShowEmailModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="modal-content"
              onClick={e => e.stopPropagation()}
            >
              <div className="modal-header">
                <h3><Mail size={20} className="icon-accent" /> Email Analysis Report</h3>
                <button className="btn-close-modal" onClick={() => setShowEmailModal(false)}>×</button>
              </div>
              <form onSubmit={handleEmailReport}>
                <p className="modal-desc">Send the full AI research dossier for <strong>{ticker}</strong> to your inbox.</p>
                <div className="modal-form-group">
                  <label>Email Address</label>
                  <input
                    type="email"
                    placeholder="name@example.com"
                    value={emailAddress}
                    onChange={e => setEmailAddress(e.target.value)}
                    required
                    autoFocus
                  />
                </div>
                <div className="modal-actions">
                  <button type="button" onClick={() => setShowEmailModal(false)} className="btn-ghost">Cancel</button>
                  <button type="submit" disabled={emailing} className="btn-primary-v2">
                    {emailing ? <Loader2 className="spinner-icon" size={18} /> : <Mail size={18} />}
                    {emailing ? 'Sending...' : 'Send Report'}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
  /* Page Layout & Core Typography */
      .analysis-page {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1.5rem;
        color: white;
        animation: fadeIn 0.5s ease-out;
      }

      .page-header {
        margin-bottom: 2rem;
        text-align: center;
      }
      .page-header h1 {
        font-size: 2rem;
      font-weight: 800;
      margin-bottom: 0.5rem;
      background: linear-gradient(135deg, #fff 30%, var(--accent-primary) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      font-family: 'Outfit', sans-serif;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
        }
      .header-icon {
        color: var(--accent-primary);
        }
      .page-header p {
        color: var(--text-dim);
      font-size: 0.9rem;
      max-width: 600px;
      margin: 0 auto;
      line-height: 1.5;
        }

      /* Loading Components */
      .loading-spinner-container {
        display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      padding: 2rem;
        }
      .spinner-icon {
        animation: spin 1s linear infinite;
      color: var(--accent-primary);
        }
      .spinner-text {
        color: var(--text-dim);
      font-size: 0.875rem;
      font-weight: 500;
        }
      @keyframes spin {
        from {transform: rotate(0deg); }
      to {transform: rotate(360deg); }
        }
      .section-card-content {
        color: rgba(255, 255, 255, 0.85);
      font-size: 0.95rem;
      line-height: normal;
        }
      .report-bullet-row {
        display: flex;
      gap: 0.75rem;
      margin-bottom: 0.75rem;
      padding-left: 0.5rem;
        }
      .bullet-dot {
        color: var(--accent-primary);
      font-size: 1.2rem;
      line-height: 1.4rem;
        }
      .bullet-text {
        flex: 1;
      line-height: 1.65;
        }
      .report-paragraph {
        margin - bottom: 1rem;
      line-height: 1.65;
        }
      .report-bold {
        color: var(--accent-secondary);
      font-weight: 700;
        }
      .theme-pastel .report-bold {
        color: var(--accent-primary) !important;
        }
      .theme-pastel .bullet-dot {
        color: var(--accent-primary) !important;
        }
      .theme-pastel .section-card-content {
        color: #374151 !important;
        }
      /* Charts Visualization */
      .skeleton-card {
        background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--glass-border);
      border-radius: 12px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
        }
      .skeleton-line {
        height: 12px;
      background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
      border-radius: 6px;
        }
      .skeleton-line.wide {width: 100%; }
      .skeleton-line.medium {width: 70%; }
      .skeleton-line.narrow {width: 40%; }
      @keyframes shimmer {
        0 % { background- position: 200% 0; }
      100% {background - position: -200% 0; }
        }

      /* Search & Discovery Section */
      .search-container {
        margin - bottom: 2.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
        }
      .ticker-form-v2 {
        display: flex;
      gap: 0.75rem;
      align-items: center;
      width: 100%;
      max-width: 600px;
      margin: 0 auto;
        }
      .ticker-input-wrapper {
        position: relative;
      flex: 1;
        }
      .ticker-input {
        width: 100%;
      background: transparent;
      border: none;
      padding: 0.75rem 1rem;
      color: var(--text-main);
      font-size: 0.9rem;
      font-family: 'Outfit', sans-serif;
      transition: all 0.2s ease;
        }
      .ticker-input:focus {
        outline: none;
        }
      .btn-fetch-v2 {
        background: linear-gradient(135deg, var(--accent-primary), #6d28d9);
      color: white;
      padding: 0.75rem 1.5rem;
      border: none;
      border-radius: 12px;
      font-weight: 600;
      font-family: 'Outfit', sans-serif;
      font-size: 0.875rem;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
      display: flex;
      align-items: center;
      gap: 0.5rem;
      white-space: nowrap;
        }
      .btn-fetch-v2:hover:not(:disabled) {
        transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
        }
      .btn-fetch-v2:disabled {
        opacity: 0.7;
      cursor: not-allowed;
        }

      .btn-secondary-v2 {
        background: rgba(255, 255, 255, 0.05);
      color: var(--text-main);
      padding: 0.6rem 1.2rem;
      border: 1px solid var(--glass-border);
      border-radius: 10px;
      font-weight: 600;
      font-family: 'Outfit';
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 0.5rem;
        }
      .btn-secondary-v2:hover {
        background: rgba(255, 255, 255, 0.1);
      border-color: var(--accent-primary);
        }

      .btn-icon-v2 {
        background: none;
      border: 1px solid var(--glass-border);
      color: var(--text-muted);
      width: 38px;
      height: 38px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s ease;
        }
      .btn-icon-v2:hover {
        border - color: var(--accent-primary);
      color: var(--text-main);
      background: rgba(124, 58, 237, 0.1);
        }

      .popular-tags {
        display: flex;
      align-items: center;
      justify-content: center;
      gap: 1rem;
      margin-top: 0.5rem;
        }
      .tags-label {font - size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }
      .tags-group {display: flex; gap: 0.5rem; flex-wrap: wrap; justify-content: center; }
      .tag-chip {
        padding: 0.35rem 0.85rem;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--glass-border);
      border-radius: 999px;
      color: var(--text-dim);
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
        }
      .tag-chip:hover {
        background: var(--accent-primary);
      color: white; /* Maintain white on primary accent for visibility */
      box-shadow: 0 0 12px var(--accent-glow);
      transform: translateY(-1px);
        }

      .ticker-input-wrapper {
        position: relative;
      width: 100%;
      background: var(--glass-bg);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border: 1px solid var(--glass-border);
      border-radius: 12px;
      display: flex;
      align-items: center;
      padding: 0.1rem 0.5rem;
      transition: all 0.3s ease;
      box-shadow: var(--shadow-premium);
        }
      .ticker-input-wrapper.focused {
        border - color: var(--accent-primary);
      box-shadow: 0 0 15px rgba(124, 58, 237, 0.2);
        }
      .stock-dropdown-v2 {
        position: absolute;
      top: calc(100% + 8px);
      left: 0;
      right: 0;
      max-height: 320px;
      overflow-y: auto;
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 12px;
      padding: 0.5rem;
      z-index: 100;
      backdrop-filter: var(--glass-blur);
      box-shadow: var(--shadow-premium);
      animation: dropdownSlide 0.2s ease-out;
        }
      @keyframes dropdownSlide {
        from {opacity: 0; transform: translateY(-8px); }
      to {opacity: 1; transform: translateY(0); }
        }
      .stock-dropdown-v2::-webkit-scrollbar {
        width: 6px;
        }
      .stock-dropdown-v2::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
      border-radius: 3px;
        }
      .stock-dropdown-v2::-webkit-scrollbar-thumb {
        background: rgba(124, 58, 237, 0.35);
      border-radius: 3px;
        }
      .stock-dropdown-v2::-webkit-scrollbar-thumb:hover {
        background: rgba(124, 58, 237, 0.5);
        }
      .dropdown-item-v2 {
        display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.65rem 0.85rem;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.15s ease;
      border: 1px solid transparent;
      margin-bottom: 2px;
        }
      .dropdown-item-v2:last-child {
        margin - bottom: 0;
        }
      .dropdown-item-v2:hover {
        background: rgba(124, 58, 237, 0.1);
      border-color: rgba(124, 58, 237, 0.2);
        }
      .dropdown-item-v2.empty {
        color: var(--text-muted);
      font-style: italic;
      cursor: default;
      justify-content: center;
      padding: 1.5rem;
      font-size: 0.85rem;
        }
      .dropdown-item-v2.empty:hover {
        background: transparent;
      border-color: transparent;
        }
      .stock-main-info {
        display: flex;
      align-items: center;
      gap: 0.75rem;
        }
      .stock-symbol-v2 {
        font - weight: 700;
      font-size: 0.8rem;
      color: var(--accent-secondary);
      background: rgba(124, 58, 237, 0.12);
      padding: 0.3rem 0.6rem;
      border-radius: 6px;
      border: 1px solid rgba(124, 58, 237, 0.2);
      font-family: 'Outfit', monospace;
      letter-spacing: 0.02em;
      min-width: 75px;
      text-align: center;
        }
      .stock-name-v2 {
        font - weight: 500;
      font-size: 0.85rem;
      color: var(--text-main);
        }
      .stock-type-v2 {
        font - size: 0.6rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: var(--accent-secondary);
      background: rgba(124, 58, 237, 0.1);
      padding: 0.4rem 1rem;
      border-radius: 10px;
      border: 1px solid rgba(124, 58, 237, 0.2);
      backdrop-filter: blur(5px);
      font-weight: 800;
        }

      /* Stock Metadata & Price Display */
      .stock-info-v2 {
        margin - bottom: 2.5rem;
      animation: slideUp 0.4s ease-out;
        }
      .company-basics {
        display: flex;
      align-items: flex-end;
      gap: 1rem;
      margin-bottom: 1.5rem;
      flex-wrap: wrap;
        }
      .header-title-row {
        display: flex;
      align-items: center;
      gap: 1.5rem;
      margin-bottom: 0.5rem;
        }
      .header-meta-row {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        align-items: center;
        flex-wrap: wrap;
      }
      .sector, .industry {
        padding: 0.35rem 0.85rem;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        display: flex; align-items: center; justify-content: center;
        transition: all 0.2s ease;
      }
      .sector {
        background: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border-color: rgba(16, 185, 129, 0.2);
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.1);
      }
      .industry {
        background: rgba(124, 58, 237, 0.1);
        color: var(--accent-secondary);
        border-color: rgba(124, 58, 237, 0.2);
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.1);
      }
      .sector:hover, .industry:hover {
        transform: translateY(-2px);
        filter: brightness(1.2);
      }
      .star-btn {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: var(--text-muted);
        width: 44px;
        height: 44px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        backdrop-filter: blur(5px);
      }
      .star-btn:hover {
        border-color: var(--accent-primary);
        color: var(--accent-primary);
        transform: scale(1.1) rotate(10deg);
        box-shadow: 0 0 20px rgba(124, 58, 237, 0.3);
        background: rgba(124, 58, 237, 0.1);
      }
      .star-btn.active {
        color: var(--accent-primary);
        border-color: var(--accent-primary);
        background: rgba(124, 58, 237, 0.15);
        box-shadow: 0 0 25px rgba(124, 58, 237, 0.25);
      }

      .company-name {
        font-size: 2.25rem;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.03em;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        margin-right: 0.5rem;
        font-family: 'Outfit';
      }

      .price-chart-section {
        margin: 2rem 0;
      min-height: 400px;
        }
      .company-meta {
        display: flex;
      gap: 0.75rem;
      margin-bottom: 0.25rem;
        }
      .ticker-badge {
        padding: 0.4rem 0.85rem;
        background: rgba(124, 58, 237, 0.1);
        border: 1px solid rgba(124, 58, 237, 0.25);
        border-radius: 8px;
        color: var(--accent-secondary);
        font-weight: 700;
        font-size: 0.8rem;
        display: flex; align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        backdrop-filter: blur(5px);
        letter-spacing: 0.03em;
      }

      .price-info {
        display: flex;
      flex-direction: column;
      gap: 1.25rem;
        }
      .current-price {
        display: flex;
      align-items: baseline;
      gap: 0.5rem;
        }
      .currency {font - size: 1.5rem; color: var(--text-dim); font-weight: 300; }
      .price {font - size: 2.75rem; font-weight: 800; line-height: 1; letter-spacing: -0.02em; }
      .change {font - size: 1rem; font-weight: 700; margin-left: 0.5rem; }
      .change.positive {color: #10b981; }
      .change.negative {color: #ef4444; }

      .price-details {
        display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 1.5rem;
      padding: 1.5rem;
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      backdrop-filter: var(--glass-blur);
      box-shadow: var(--shadow-premium);
        }
      .detail {display: flex; flex-direction: column; gap: 0.5rem; transition: transform 0.3s ease; }
      .detail:hover {transform: translateY(-3px); }
      .detail .label {font - size: 0.7rem; text-transform: uppercase; color: var(--text-muted); font-weight: 800; letter-spacing: 0.12em; opacity: 0.8; }
      .detail .value {font - size: 1.25rem; font-weight: 800; font-family: 'Outfit'; color: var(--text-main); }

      /* Tabs & Analysis Controls */
      .analysis-tabs {
        display: flex;
      gap: 0.5rem;
      margin: 1.5rem 0 1.25rem;
      padding: 0.4rem;
      background: rgba(124, 58, 237, 0.05);
      backdrop-filter: blur(10px);
      border-radius: 14px;
      border: 1px solid rgba(124, 58, 237, 0.2);
      width: fit-content;
      box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
        }
      .tab {
        padding: 0.6rem 1.25rem;
      border-radius: 10px;
      border: 1px solid transparent;
      background: transparent;
      color: var(--text-dim);
      font-weight: 600;
      font-family: 'Outfit';
      cursor: pointer;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.85rem;
        }
      .tab:hover:not(.active) {
        background: rgba(124, 58, 237, 0.1);
      color: var(--accent-primary);
        }
      .tab.active {
        background: var(--accent-primary);
      color: white; /* Active tab text remains white for contrast against accent-primary */
      border: 1px solid rgba(124, 58, 237, 0.4);
      backdrop-filter: blur(5px);
      box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2);
        }

      .btn-primary-v2 {
        display: flex;
      align-items: center;
      gap: 0.6rem;
      background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
      border: none;
      color: white; /* Button text remains white for contrast against gradients */
      padding: 0.6rem 1.25rem;
      border-radius: 10px;
      font-weight: 700;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
      font-family: 'Outfit', sans-serif;
        }

      .btn-primary-v2:hover {
        transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(124, 58, 237, 0.45);
      filter: brightness(1.1);
        }

      .btn-primary-v2:active {
        transform: translateY(0);
        }

      .full-analysis-controls, .quick-analysis-buttons {
        padding: 2rem;
        background: rgba(15, 15, 20, 0.6);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        display: flex;
        flex-direction: column;
        gap: 2rem;
        animation: fadeIn 0.5s ease-out;
        box-shadow: 0 20px 50px -10px rgba(0, 0, 0, 0.5);
      }

      .forecast-params label {font - size: 0.95rem; font-weight: 600; color: var(--text-dim); margin-bottom: 1rem; display: block; }
      .forecast-params label strong {color: var(--text-main); border-bottom: 2px solid var(--accent-primary); padding-bottom: 2px; }
      .forecast-options {display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.75rem; }
      .option-btn {
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.03);
        color: var(--text-dim);
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
        font-size: 0.9rem;
        letter-spacing: 0.02em;
      }
      .option-btn:hover { border-color: rgba(124, 58, 237, 0.4); background: rgba(124, 58, 237, 0.05); color: var(--text-main); }
      .option-btn.active {
        background: var(--accent-primary);
        color: white; 
        border-color: var(--accent-primary);
        box-shadow: 0 4px 20px rgba(124, 58, 237, 0.4);
        transform: translateY(-1px);
        font-weight: 700;
      }

      /* Custom Questions Section */
      .custom-questions-section {
        margin-top: 1.5rem;
        padding: 1.25rem;
        border-radius: 16px;
        background: rgba(124, 58, 237, 0.03);
        border: 1px solid rgba(124, 58, 237, 0.1);
      }
      .custom-questions-section label {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-dim);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
      }
      .custom-questions-input {
        width: 100%;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(0, 0, 0, 0.3);
        color: var(--text-main);
        font-family: inherit;
        font-size: 0.9rem;
        resize: vertical;
        min-height: 80px;
        transition: all 0.2s;
      }
      .custom-questions-input:focus {
        outline: none;
        border-color: var(--accent-primary);
        box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15);
      }
      .custom-questions-input::placeholder {
        color: rgba(255, 255, 255, 0.3);
      }

      .document-selection h3 {font - size: 1rem; font-weight: 700; margin-bottom: 0.5rem; }
      .selection-hint {font - size: 0.8rem; color: var(--text-muted); margin-bottom: 1rem; }
      .docs-grid {
        display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 0.75rem;
        }
      .doc-item {
        padding: 1.25rem;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        cursor: pointer;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
        position: relative;
        overflow: hidden;
        min-height: 120px;
        justify-content: center;
      }
      .doc-item::before {
        content: "";
      position: absolute;
      top: 0; left: 0; width: 100%; height: 100%;
      background: linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, transparent 100%);
      opacity: 0;
      transition: opacity 0.3s ease;
        }
      .doc-item:hover {
        border - color: rgba(124, 58, 237, 0.3);
      transform: translateY(-4px) scale(1.02);
      background: var(--bg-dark-700);
        }
      .doc-item:hover::before {opacity: 1; }
      .doc-item.selected {
        border-color: var(--accent-primary);
        background: rgba(124, 58, 237, 0.1);
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.3), 0 8px 30px rgba(124, 58, 237, 0.15);
        transform: translateY(-2px);
      }
      .doc-item.selected .doc-name {color: var(--accent-secondary); }
      .doc-name {font - weight: 700; font-size: 0.9rem; color: var(--text-main); position: relative; z-index: 1; }
      .doc-type {font - size: 0.65rem; text-transform: uppercase; color: var(--text-muted); font-weight: 800; letter-spacing: 0.1em; position: relative; z-index: 1; }

      .btn-analyze {
        width: 100%;
        padding: 1.25rem;
        background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
        color: white; 
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        font-size: 1.1rem;
        font-weight: 800;
        font-family: 'Outfit';
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
        box-shadow: 0 10px 20px -5px rgba(139, 92, 246, 0.5), inset 0 0 0 1px rgba(255,255,255,0.1);
        display: flex; align-items: center; justify-content: center; gap: 0.75rem;
        position: relative;
        overflow: hidden;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
      }
      .btn-analyze::after {
        content: "";
      position: absolute;
      top: -50%; left: -50%; width: 200%; height: 200%;
      background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%);
      opacity: 0;
      transition: opacity 0.4s ease;
      pointer-events: none;
        }
      .btn-analyze:hover:not(:disabled) {
        transform: translateY(-4px) scale(1.02);
      box-shadow: 0 20px 40px rgba(124, 58, 237, 0.6), 0 0 0 2px rgba(124, 58, 237, 0.3);
      filter: brightness(1.1);
        }
      .btn-analyze:hover::after {opacity: 1; }
      .btn-analyze:active {transform: translateY(0) scale(0.98); }

      .quick-analysis-buttons {
        display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 0.75rem;
        }
      .btn-quick {
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        color: var(--text-main);
        font-family: 'Outfit';
        font-weight: 700;
        font-size: 0.95rem;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
        display: flex; flex-direction: column; align-items: center; gap: 0.8rem;
        min-height: 140px;
        justify-content: center;
      }
      .btn-quick:hover:not(:disabled) {
        background: var(--bg-dark-700);
      border-color: var(--accent-primary);
      transform: translateY(-6px);
      box-shadow: 0 15px 30px rgba(0,0,0,0.5), 0 0 15px rgba(124, 58, 237, 0.3);
        }

      /* Analyzing Overlay */
      .analyzing-overlay {
        margin - top: 1.5rem;
      padding: 2rem;
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 16px;
      backdrop-filter: blur(20px);
      text-align: center;
        }
      .analyzing-content h3 {
        font - size: 1.1rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
      color: var(--text-main);
        }
      .analyzing-content p {
        font - size: 0.8rem;
      color: var(--text-muted);
      margin-bottom: 1.25rem;
        }
      .analyzing-spinner {
        margin - bottom: 1rem;
        }
      .main-spinner {
        color: var(--accent-primary);
      animation: spin 1s linear infinite;
        }
      .analyzing-steps {
        display: flex;
      gap: 0.75rem;
      justify-content: center;
      flex-wrap: wrap;
        }
      .analyzing-steps .step {
        padding: 0.4rem 0.75rem;
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 8px;
      font-size: 0.7rem;
      font-weight: 600;
      color: var(--text-muted);
      transition: all 0.3s ease;
        }
      .analyzing-steps .step.active {
        background: rgba(124, 58, 237, 0.15);
      border-color: var(--accent-primary);
      color: var(--accent-secondary);
      animation: pulse 1.5s ease-in-out infinite;
        }
      @keyframes pulse {
        0 %, 100 % { opacity: 1; }
          50% {opacity: 0.6; }
        }

      /* Results & Report Aesthetics */
      .analysis-results {margin - top: 3rem; }
      .results-header h2 {font - size: 1.5rem; font-weight: 800; margin-bottom: 1.25rem; letter-spacing: -0.02em; }

      .result-cards-grid {
        display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.25rem;
        }

      .rating-badge {
        font - size: 2rem;
      font-weight: 800;
      padding: 1rem;
      border-radius: 14px;
      text-align: center;
      margin: 1rem 0;
      box-shadow: 0 8px 25px rgba(0,0,0,0.1);
      color: white; /* Rating value is white on its colorful background */
        }

      .icon-gold {color: #f59e0b; filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.4)); }
      .icon-accent {color: var(--accent-primary); }
      .card-header-row {
        display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
        }

      .risk-badge {
        font - size: 0.7rem;
      font-weight: 700;
      padding: 0.35rem 0.75rem;
      border-radius: 20px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
        }
      .risk-badge.low {background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
      .risk-badge.moderate {background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
      .risk-badge.high {background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }

      .risk-level {
        display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.85rem;
      margin-top: 1rem;
        }
      .risk-text {font - weight: 700; color: var(--text-main); }

      /* Missing Card Styles */
      .results-header {
        display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
        }

      /* Recommendation Card Details */
      .recommendation-card {display: flex; flex-direction: column; gap: 1rem; }
      .confidence-meter {display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem; }
      .meter-label {display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600; color: var(--text-dim); }
      .meter-track {height: 6px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
      .meter-fill {height: 100%; background: var(--accent-primary); border-radius: 4px; box-shadow: 0 0 10px rgba(124, 58, 237, 0.4); }

      /* Market Vitals Card Details */
      .vitals-grid {display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem; }
      .vital-item {display: flex; flex-direction: column; gap: 0.25rem; padding: 1rem; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid var(--glass-border); justify-content: center; }
      .vital-label {font - size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); font-weight: 700; }
      .vital-value-row {display: flex; align-items: baseline; gap: 0.5rem; margin: 0.25rem 0; }
      .vital-value {font - size: 1.4rem; font-weight: 800; color: var(--text-main); line-height: 1; }
      .vital-value.violet {color: var(--accent-primary); }
      .vital-sub {font - size: 0.75rem; color: var(--text-dim); }
      .sentiment-label {display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px; font-weight: 700; font-size: 0.75rem; margin-top: 0.25rem; text-align: center; width: fit-content; }
      .sentiment-label.positive {color: #10b981; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.2); }
      .sentiment-label.negative {color: #ef4444; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.2); }
      .sentiment-label.neutral {color: #f59e0b; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.2); }

      /* Price Outlook Card Details */
      .forecast-summary-card {display: flex; flex-direction: column; }
      .outlook-data {display: flex; flex-direction: column; gap: 1.5rem; margin-top: 1rem; flex: 1; justify-content: center; }
      .outlook-price {display: flex; flex-direction: column; gap: 0.25rem; }
      .price-label {font - size: 0.8rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
      .price-value {font - size: 1.8rem; font-weight: 800; color: var(--text-main); letter-spacing: -0.02em; }
      .outlook-trend {display: flex; align-items: center; gap: 0.5rem; font-weight: 800; font-size: 1rem; padding: 0.6rem 1rem; background: var(--glass-bg); border-radius: 10px; width: fit-content; }
      .outlook-trend.bullish {color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.1); }
      .outlook-trend.bearish {color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); background: rgba(239, 68, 68, 0.1); }
      .outlook-trend.neutral {color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); background: rgba(245, 158, 11, 0.1); }

      /* HIGH-FIDELITY MODULES - THE CORE REPORT UI */
      .report-preview-container {margin - top: 3rem; }
      .report-sections-grid {
        display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 1.5rem;
        }
      .report-section-card {
        padding: 1.5rem !important;
      border: 1px solid var(--glass-border);
      border-radius: 16px;
      background: var(--glass-bg);
      transition: all 0.3s ease;
        }
      .report-section-card:hover {border - color: var(--accent-primary); transform: translateY(-5px); box-shadow: var(--shadow-premium); }

      .section-card-header {display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem; }
      .section-title-group {display: flex; align-items: center; gap: 0.75rem; }
      .section-number {font - size: 2rem; font-weight: 900; color: var(--accent-primary); opacity: 0.1; line-height: 0.9; }
      .section-icon {
        width: 36px; height: 36px;
      border-radius: 10px;
      background: rgba(124, 58, 237, 0.08);
      border: 1px solid var(--glass-border);
      display: flex; align-items: center; justify-content: center;
      color: var(--accent-secondary);
      box-shadow: 0 0 15px rgba(124, 58, 237, 0.1);
        }

      .radar-module {background: var(--glass-bg); border-radius: 14px; padding: 1rem; margin-bottom: 1rem; border: 1px solid var(--glass-border); }
      .radar-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        justify-content: center;
        padding: 1rem;
        border-top: 1px solid rgba(255,255,255,0.06);
        margin-top: 0.5rem;
      }
      .radar-legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.75rem;
        background: rgba(255,255,255,0.03);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid transparent;
      }
      .radar-legend-item:hover {
        background: rgba(124, 58, 237, 0.1);
        border-color: rgba(124, 58, 237, 0.3);
        transform: translateY(-2px);
      }
      .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
      }
      .legend-label {
        font-size: 0.75rem;
        color: var(--text-dim);
        font-weight: 500;
      }
      .legend-value {
        font-size: 0.8rem;
        font-weight: 700;
        color: var(--text-main);
      }

      .signals-grid {display: flex; flex-direction: column; gap: 1rem; margin: 1.25rem 0; }
      .signal-item {display: flex; flex-direction: column; gap: 0.5rem; }
      .signal-meta {display: flex; justify-content: space-between; font-weight: 700; font-size: 0.85rem; color: var(--text-dim); }
      .signal-bar-bg {height: 10px; background: rgba(255,255,255,0.05); border-radius: 5px; overflow: hidden; border: 1px solid rgba(255,255,255,0.02); }
      .signal-bar-fill {height: 100%; border-radius: 5px; box-shadow: 0 0 12px rgba(16, 185, 129, 0.4); position: relative; }
      .signal-bar-fill::after {content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent); animation: shine 2s infinite; }

      .actions-stepper {display: flex; flex-direction: column; margin: 1.25rem 0; }
      .step-item {display: flex; gap: 1rem; }
      .step-line-wrapper {display: flex; flex-direction: column; align-items: center; width: 28px; }
      .step-dot {
        width: 28px; height: 28px;
      background: rgba(16, 185, 129, 0.1);
      border: 2px solid rgba(16, 185, 129, 0.6);
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      color: #10b981;
      box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
        }
      .step-line {width: 2px; background: var(--glass-border); flex: 1; margin: 6px 0; border-radius: 1px; }
      .step-content {padding - bottom: 1.5rem; flex: 1; }
      .step-badge {
        font - size: 0.65rem; font-weight: 700; text-transform: uppercase;
      color: #10b981; background: rgba(16, 185, 129, 0.12);
      padding: 0.25rem 0.6rem; border-radius: 5px; margin-bottom: 0.5rem; display: inline-block;
      border: 1px solid rgba(16, 185, 129, 0.25);
        }
      .step-content p {font - size: 0.85rem; line-height: 1.6; color: var(--text-dim); }

      .full-width-chart {margin - top: 2rem; grid-column: 1 / -1; }
      .forecast-chart-container {
        margin - top: 1.25rem;
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid var(--glass-border);
      background: var(--glass-bg);
      box-shadow: var(--shadow-premium);
        }
      .forecast-chart-img {width: 100%; height: auto; display: block; filter: contrast(1.05) brightness(1.1) saturate(1.05); }

      @keyframes shine {from {left: -100%; } to {left: 100%; } }
      @keyframes fadeIn {from {opacity: 0; transform: translateY(15px); } to {opacity: 1; transform: translateY(0); } }
      @keyframes slideUp {from {opacity: 0; transform: translateY(25px); } to {opacity: 1; transform: translateY(0); } }

      /* Theme Toggle Styles */
      .page-header {
        display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
        }
      .header-main {text - align: left; }
      .header-main h1 {justify - content: flex-start; color: var(--text-main); }
      .header-main p {color: var(--text-dim); }
      .theme-toggle {
        display: flex;
      gap: 0.5rem;
      padding: 0.25rem;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      border: 1px solid var(--glass-border);
        }
      .theme-btn {
        padding: 0.5rem 0.75rem;
      border: none;
      background: transparent;
      border-radius: 8px;
      color: var(--text-dim);
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 0.25rem;
        }
      .theme-btn:hover {color: var(--accent-primary); background: rgba(124, 58, 237, 0.1); }
      .theme-btn.active {
        background: var(--accent-primary);
      color: white; /* Active theme button remains white */
      box-shadow: 0 0 15px rgba(147, 51, 234, 0.4);
        }

      /* Section Numbers - More Visible */
      .section-number {
        font - size: 1.8rem !important;
      font-weight: 800 !important;
      font-family: 'Outfit', sans-serif !important;
      color: var(--accent-primary) !important;
      opacity: 0.9 !important;
      margin-right: 0.75rem;
      text-shadow: 0 0 20px rgba(147, 51, 234, 0.5);
        }

      /* Purged pastel theme overrides to favor global variables */

      /* Badges */
      .theme-pastel .badge-neural,
      .theme-pastel .badge-premium {
        background: #f3e8ff !important;
      color: #7c3aed !important;
      border-color: rgba(139, 92, 246, 0.3) !important;
        }

      /* Theme toggle */
      .theme-pastel .theme-toggle {
        background: white !important;
      border-color: rgba(139, 92, 246, 0.2) !important;
        }
      .theme-pastel .theme-btn {color: #6b7280 !important; }
      .theme-pastel .theme-btn:hover {
        background: #f3e8ff !important;
      color: #8b5cf6 !important;
        }
      .theme-pastel .theme-btn.active {
        background: #8b5cf6 !important;
      color: white !important;
        }

      `}</style>
    </div >
  )
}
