import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Bike,
  Check,
  CircleHelp,
  Clock3,
  Gauge,
  LayoutDashboard,
  MapPin,
  Menu,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Truck,
  X,
} from 'lucide-react'
import { getModelComparison, getLiveStations } from './services/api'

const statusStyles = {
  shortage: 'status-shortage',
  balanced: 'status-balanced',
  surplus: 'status-surplus',
  no_data: 'status-no-data',
}

const statusLabels = {
  shortage: 'Shortage',
  balanced: 'Balanced',
  surplus: 'Surplus',
  no_data: 'Awaiting data',
}

const SIDEBAR_KEY = 'cycleflow.sidebarOpen'

function getInitialSidebarState() {
  if (typeof window !== 'undefined' && window.innerWidth < 1024) return false
  try {
    const saved = localStorage.getItem(SIDEBAR_KEY)
    return saved === null ? true : saved === 'true'
  } catch {
    return true
  }
}

function getTransferNeed(station) {
  if (station.status !== 'shortage' || station.available_bikes === null) return 0
  const thresholdToBalance = Math.floor(station.capacity * 0.2) + 1
  return Math.max(0, thresholdToBalance - station.available_bikes)
}

function getTransferSurplus(station) {
  if (station.status !== 'surplus' || station.available_bikes === null) return 0
  const bikesToKeep = Math.ceil(station.capacity * 0.8) - 1
  return Math.max(0, station.available_bikes - bikesToKeep)
}

function buildRedistributionPlan(stations) {
  const recipients = stations
    .filter((station) => station.status === 'shortage')
    .map((station) => ({ station, remaining: getTransferNeed(station) }))
    .sort((a, b) => b.remaining - a.remaining)
  const donors = stations
    .filter((station) => station.status === 'surplus')
    .map((station) => ({ station, remaining: getTransferSurplus(station) }))
    .sort((a, b) => b.remaining - a.remaining)
  const plan = []

  recipients.forEach((recipient) => {
    donors.forEach((donor) => {
      if (recipient.remaining <= 0 || donor.remaining <= 0) return
      const bikes = Math.min(recipient.remaining, donor.remaining)
      plan.push({
        from: donor.station,
        to: recipient.station,
        bikes,
      })
      recipient.remaining -= bikes
      donor.remaining -= bikes
    })
  })

  return plan
}

function StatCard({ title, value, detail, icon: Icon, tone }) {
  return (
    <article className="stat-card">
      <div className={`stat-icon ${tone}`}>
        <Icon size={19} strokeWidth={2} />
      </div>
      <p className="stat-label">{title}</p>
      <div className="stat-value">{value}</div>
      <p className="stat-detail">{detail}</p>
    </article>
  )
}

function SectionHeading({ eyebrow, title, detail, action }) {
  return (
    <div className="section-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        {detail && <p className="section-detail">{detail}</p>}
      </div>
      {action}
    </div>
  )
}

function StatusBadge({ status }) {
  return (
    <span className={`status-badge ${statusStyles[status] || statusStyles.no_data}`}>
      <span className="status-dot" />
      {statusLabels[status] || status}
    </span>
  )
}

function StationCard({ station }) {
  const hasSnapshot = station.available_bikes !== null
  const percentage = hasSnapshot ? Number(station.bike_percentage) : null
  const need = getTransferNeed(station)
  const surplus = getTransferSurplus(station)
  const recommendation = {
    shortage: need > 0
      ? `Dispatch ${need} ${need === 1 ? 'bike' : 'bikes'} to move above the 20% threshold.`
      : 'Dispatch a bike to move above the shortage threshold.',
    surplus: surplus > 0
      ? `Stage up to ${surplus} ${surplus === 1 ? 'bike' : 'bikes'} for redistribution.`
      : 'Review inventory for a potential transfer.',
    balanced: 'No transfer needed. Continue routine monitoring.',
    no_data: 'Verify station telemetry before planning a dispatch.',
  }[station.status] || 'Review the station status.'

  return (
    <article className={`station-card station-card-${station.status}`}>
      <div className="station-card-top">
        <div className="station-identity">
          <span className="station-pin"><MapPin size={16} /></span>
          <div className="station-names">
            <h3 title={station.station_name}>{station.station_name}</h3>
            <span>{station.station_id}</span>
          </div>
        </div>
        <StatusBadge status={station.status} />
      </div>

      <div className="bike-count-row">
        <div>
          <span className="data-caption">Bikes available</span>
          <p className="bike-count">
            {station.available_bikes ?? '—'}
            <span> / {station.capacity}</span>
          </p>
        </div>
        <div className="occupancy-value">
          <span className="data-caption">Occupancy</span>
          <strong>{hasSnapshot ? `${percentage}%` : '—'}</strong>
        </div>
      </div>

      <div className="station-meta">
        <span><Bike size={14} /> E-bikes <strong>{station.available_e_bikes ?? '—'}</strong></span>
        <span><Bike size={14} /> Mechanical <strong>{station.available_mechanical_bikes ?? '—'}</strong></span>
      </div>

      <div
        className="occupancy-track"
        role="progressbar"
        aria-label={`${station.station_name} occupancy`}
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={hasSnapshot ? Math.min(percentage, 100) : 0}
      >
        <span
          className={`occupancy-fill fill-${station.status}`}
          style={{ width: `${hasSnapshot ? Math.min(Math.max(percentage, 0), 100) : 0}%` }}
        />
      </div>

      <div className="station-meta">
        <span><Bike size={14} /> Capacity <strong>{station.capacity ?? '—'}</strong></span>
        <span><Activity size={14} /> Docks <strong>{station.available_docks ?? '—'}</strong></span>
      </div>
      <div className="station-meta">
        <span><Gauge size={14} /> Source <strong>{station.source === 'capital_bikeshare_gbfs' ? 'Official GBFS' : station.source || 'Local'}</strong></span>
        <span><Clock3 size={14} /> Status <strong>{station.station_status || station.status || 'unknown'}</strong></span>
      </div>

      <div className={`station-recommendation recommendation-${station.status}`}>
        <span className="recommendation-icon">
          {station.status === 'shortage'
            ? <ArrowDownRight size={16} />
            : station.status === 'surplus'
              ? <ArrowUpRight size={16} />
              : station.status === 'balanced'
                ? <Check size={16} />
                : <CircleHelp size={16} />}
        </span>
        <p>{recommendation}</p>
      </div>
    </article>
  )
}

function NavLink({ href, icon: Icon, children, active, onClick }) {
  return (
    <a
      href={href}
      className={`nav-link${active ? ' nav-link-active' : ''}`}
      onClick={onClick}
    >
      <Icon size={18} strokeWidth={1.8} />
      {children}
    </a>
  )
}

function App() {
  const [stations, setStations] = useState([])
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(true)
  const [modelsLoading, setModelsLoading] = useState(true)
  const [error, setError] = useState('')
  const [modelError, setModelError] = useState('')
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [lastUpdated, setLastUpdated] = useState(null)
  const [liveStatus, setLiveStatus] = useState({
    fetch_status: 'unknown',
    stale: true,
    last_successful_fetch: null,
  })
  const [sidebarOpen, setSidebarOpen] = useState(getInitialSidebarState)

  const toggleSidebar = useCallback(() => {
    setSidebarOpen((open) => {
      const next = !open
      try {
        if (window.innerWidth >= 1024) {
          localStorage.setItem(SIDEBAR_KEY, String(next))
        }
      } catch {
        // Storage may be unavailable in private browsing.
      }
      return next
    })
  }, [])

  const loadStations = useCallback(async () => {
    try {
      const payload = await getLiveStations()
      const liveStations = Array.isArray(payload?.stations) ? payload.stations : []
      setStations(liveStations)
      setError(payload?.fetch_status === 'error' ? 'The latest live feed is currently unavailable.' : '')
      setLiveStatus({
        fetch_status: payload?.fetch_status || 'unknown',
        stale: Boolean(payload?.stale),
        last_successful_fetch: payload?.last_successful_fetch || null,
      })
      setLastUpdated(payload?.last_successful_fetch ? new Date(payload.last_successful_fetch) : new Date())
    } catch (err) {
      setStations([])
      setError(err.message || 'Could not connect to the backend.')
      setLiveStatus({ fetch_status: 'error', stale: true, last_successful_fetch: null })
    } finally {
      setLoading(false)
    }
  }, [])

  const loadModels = useCallback(async () => {
    try {
      const data = await getModelComparison()
      if (!Array.isArray(data)) throw new Error('The model report returned an unexpected response.')
      setModels(data)
      setModelError('')
    } catch (err) {
      setModelError(err.message || 'Could not load the model comparison report.')
    } finally {
      setModelsLoading(false)
    }
  }, [])

  useEffect(() => {
    const initialLoad = window.setTimeout(() => {
      loadStations()
      loadModels()
    }, 0)
    const interval = window.setInterval(() => {
      setLoading(true)
      loadStations()
    }, 60_000)
    return () => {
      window.clearTimeout(initialLoad)
      window.clearInterval(interval)
    }
  }, [loadModels, loadStations])

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === 'Escape' && window.innerWidth < 1024) setSidebarOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const knownStations = useMemo(
    () => stations.filter((station) => station.available_bikes !== null),
    [stations],
  )
  const totalBikes = knownStations.reduce(
    (sum, station) => sum + (Number(station.available_bikes) || 0),
    0,
  )
  const shortageCount = stations.filter((station) => station.status === 'shortage').length
  const balancedCount = stations.filter((station) => station.status === 'balanced').length
  const surplusCount = stations.filter((station) => station.status === 'surplus').length
  const averageOccupancy = knownStations.length
    ? Math.round(knownStations.reduce(
      (sum, station) => sum + (Number(station.bike_percentage) || 0),
      0,
    ) / knownStations.length)
    : 0

  const filteredStations = useMemo(() => {
    const query = search.trim().toLowerCase()
    return stations.filter((station) => {
      const matchesSearch = !query
        || station.station_name.toLowerCase().includes(query)
        || station.station_id.toLowerCase().includes(query)
      return matchesSearch && (filter === 'all' || station.status === filter)
    })
  }, [filter, search, stations])

  const redistributionPlan = useMemo(
    () => buildRedistributionPlan(stations),
    [stations],
  )
  const bestModel = models.reduce((best, model) => (
    !best || Number(model.RMSE) < Number(best.RMSE) ? model : best
  ), null)
  const pulseStations = [...knownStations]
    .sort((a, b) => Number(b.bike_percentage) - Number(a.bike_percentage))
    .slice(0, 6)

  return (
    <div className="app-shell">
      <div
        onClick={() => setSidebarOpen(false)}
        aria-hidden="true"
        className={`sidebar-backdrop${sidebarOpen ? ' backdrop-visible' : ''}`}
      />

      <aside className={`sidebar${sidebarOpen ? ' sidebar-open' : ''}`} aria-label="Main navigation">
        <div className="brand">
          <a className="brand-main" href="#overview" onClick={() => setSidebarOpen(false)}>
            <span className="brand-mark"><Bike size={23} strokeWidth={2.1} /></span>
            <span className="brand-copy">
              <strong>cycleflow<span>.</span></strong>
              <small>URBAN MOBILITY INTELLIGENCE</small>
            </span>
          </a>
          <button
            className="sidebar-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>

        <div className="workspace-label">CONTROL CENTER</div>
        <nav className="primary-nav">
          <NavLink href="#overview" icon={LayoutDashboard} active onClick={() => setSidebarOpen(false)}>
            Overview
          </NavLink>
          <NavLink href="#stations" icon={MapPin} onClick={() => setSidebarOpen(false)}>
            Station network
          </NavLink>
          <NavLink href="#forecast" icon={Activity} onClick={() => setSidebarOpen(false)}>
            Forecast &amp; models
          </NavLink>
          <NavLink href="#redistribution" icon={Truck} onClick={() => setSidebarOpen(false)}>
            Redistribution
          </NavLink>
        </nav>

        <div className="sidebar-bottom">
          <div className={`sidebar-health${error ? ' health-error' : ''}`}>
            <span className="health-icon"><ShieldCheck size={18} /></span>
            <div>
              <strong>{error ? 'Connection issue' : 'System monitoring'}</strong>
              <span>{error ? 'API needs attention' : 'Station API connected'}</span>
            </div>
            <span className="health-indicator" />
          </div>
          <p className="sidebar-footnote">SMART BIKE DEMAND SYSTEM <span>·</span> LIVE OPERATIONS</p>
        </div>
      </aside>

      <main className={`main-content${sidebarOpen ? ' main-content-shifted' : ''}`}>
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="icon-button menu-button"
              onClick={toggleSidebar}
              aria-label={sidebarOpen ? 'Hide navigation' : 'Show navigation'}
              aria-expanded={sidebarOpen}
            >
              <Menu size={19} />
            </button>
            <div className="breadcrumbs"><span>Operations</span><span className="breadcrumb-slash">/</span> Fleet overview</div>
          </div>
          <div className="topbar-right">
            <span className={`connection-pill${error || liveStatus.stale ? ' connection-error' : ''}`}>
              <span className="live-dot" />
              {error ? 'API attention' : liveStatus.stale ? 'Stale snapshot' : 'Live system'}
            </span>
            <span className="topbar-divider" />
            <div className="operator">
              <span className="operator-avatar">FO</span>
              <span><strong>Fleet operator</strong><small>Operations</small></span>
            </div>
          </div>
        </header>

        <div className="dashboard-content">
          <section id="overview" className="welcome-row">
            <div>
              <p className="eyebrow">CITY MOBILITY · OPERATIONS CENTER</p>
              <h1>Your fleet, <span>in motion.</span></h1>
              <p className="welcome-description">
                A real-time view of station health, bike availability and where your team can make a difference.
              </p>
            </div>
            <div className="refresh-block">
              <span className="updated-label">
                <Clock3 size={14} />
                {lastUpdated
                  ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
                  : loading ? 'Connecting to station network' : 'Waiting for station data'}
                {liveStatus.stale && !error ? ' · stale snapshot' : ''}
              </span>
              <button
                className="refresh-button"
                onClick={() => {
                  setLoading(true)
                  loadStations()
                }}
                disabled={loading}
              >
                <RefreshCw size={15} className={loading ? 'spin' : ''} />
                Refresh network
              </button>
            </div>
          </section>

          {error && (
            <div className="error-banner" role="alert">
              <AlertTriangle size={18} />
              <span>{error}. Check that FastAPI is running on port 8000.</span>
              <button
                onClick={() => {
                  setLoading(true)
                  loadStations()
                }}
              >
                Retry connection
              </button>
            </div>
          )}

          <section className="stats-grid" aria-label="Fleet summary">
            <StatCard
              title="Total stations"
              value={loading && stations.length === 0 ? '—' : stations.length}
              detail={`${knownStations.length} reporting live snapshots`}
              icon={MapPin}
              tone="tone-blue"
            />
            <StatCard
              title="Balanced"
              value={balancedCount}
              detail="Within operating range"
              icon={Check}
              tone="tone-green"
            />
            <StatCard
              title="Shortage"
              value={shortageCount}
              detail="Stations below 20% capacity"
              icon={ArrowDownRight}
              tone="tone-red"
            />
            <StatCard
              title="Surplus"
              value={surplusCount}
              detail="Stations above 80% capacity"
              icon={ArrowUpRight}
              tone="tone-amber"
            />
            <StatCard
              title="System health"
              value={error ? 'Attention' : lastUpdated ? 'Online' : loading ? 'Checking' : 'Offline'}
              detail={error ? 'Station API unavailable' : 'Station API connection'}
              icon={Gauge}
              tone={error ? 'tone-red' : 'tone-green'}
            />
          </section>

          <section className="network-ribbon" aria-label="Fleet snapshot">
            <div className="ribbon-copy">
              <span className="ribbon-icon"><Bike size={19} /></span>
              <span><strong>{totalBikes.toLocaleString()}</strong><small>bikes available across reporting stations</small></span>
            </div>
            <div className="ribbon-divider" />
            <div className="ribbon-copy">
              <span className="ribbon-icon ribbon-icon-light"><Activity size={18} /></span>
              <span><strong>{knownStations.length ? `${averageOccupancy}%` : '—'}</strong><small>average station occupancy</small></span>
            </div>
            <span className="snapshot-note"><span className="live-dot" /> Snapshot-based monitoring · auto-refreshes every 60 seconds</span>
          </section>

          <section className="analytics-grid" aria-label="Network analytics">
            <article className="panel pulse-panel">
              <SectionHeading
                eyebrow="LIVE NETWORK"
                title="Capacity pulse"
                detail="Station occupancy from the latest available snapshot."
                action={<span className="panel-count">{knownStations.length} reporting</span>}
              />
              {pulseStations.length > 0 ? (
                <div className="pulse-list">
                  {pulseStations.map((station) => (
                    <div className="pulse-row" key={station.station_id}>
                      <span className="pulse-name" title={station.station_name}>{station.station_name}</span>
                      <span className="pulse-track"><span
                        className={`pulse-fill fill-${station.status}`}
                        style={{ width: `${Math.min(Math.max(Number(station.bike_percentage) || 0, 0), 100)}%` }}
                      /></span>
                      <strong className="pulse-value">{station.bike_percentage}%</strong>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-inline">{loading ? 'Loading station snapshots…' : 'No station snapshots are available yet.'}</div>
              )}
              {knownStations.length > pulseStations.length && (
                <p className="panel-footnote">Showing highest-occupancy stations · all stations are listed below.</p>
              )}
              <div className="capacity-legend">
                <span><i className="legend-dot legend-low" /> Low &lt;20%</span>
                <span><i className="legend-dot legend-balanced" /> Balanced</span>
                <span><i className="legend-dot legend-high" /> High &gt;80%</span>
              </div>
            </article>

            <article className="panel intelligence-panel" id="forecast">
              <div className="intelligence-top">
                <span className="intelligence-icon"><Sparkles size={18} /></span>
                <span className="intelligence-label">FORECAST INTELLIGENCE</span>
                <span className="evaluation-tag">MODEL EVALUATION</span>
              </div>
              {modelsLoading ? (
                <div className="intelligence-main"><strong>Loading model report…</strong></div>
              ) : modelError ? (
                <div className="intelligence-main">
                  <strong>Model report unavailable</strong>
                  <p>{modelError}</p>
                </div>
              ) : bestModel ? (
                <>
                  <div className="intelligence-main">
                    <span>Best model by lowest RMSE</span>
                    <strong>{bestModel.Model}</strong>
                    <p>Evaluation R² <b>{Number(bestModel.R2_Score).toFixed(4)}</b> · MAPE <b>{Number(bestModel['MAPE (%)']).toFixed(2)}%</b></p>
                  </div>
                  <div className="intelligence-metrics">
                    <div><span>MAE</span><strong>{Number(bestModel.MAE).toFixed(2)}</strong></div>
                    <div><span>RMSE</span><strong>{Number(bestModel.RMSE).toFixed(2)}</strong></div>
                    <div><span>R² score</span><strong>{Number(bestModel.R2_Score).toFixed(4)}</strong></div>
                  </div>
                </>
              ) : (
                <div className="intelligence-main"><strong>No evaluation results available</strong></div>
              )}
              <p className="intelligence-note">
                Metrics are from the saved ML evaluation report. Live demand predictions are not currently exposed by the API.
              </p>
            </article>
          </section>

          <section id="stations" className="stations-section">
            <SectionHeading
              eyebrow="THE CITY NETWORK"
              title="Station overview"
              detail="Every station, its live capacity and the next operational step."
              action={
                <div className="station-controls">
                  <label className="search-control">
                    <Search size={16} />
                    <input
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      placeholder="Search stations"
                      aria-label="Search stations"
                    />
                  </label>
                  <select
                    value={filter}
                    onChange={(event) => setFilter(event.target.value)}
                    aria-label="Filter stations by status"
                  >
                    <option value="all">All statuses</option>
                    <option value="shortage">Shortage</option>
                    <option value="balanced">Balanced</option>
                    <option value="surplus">Surplus</option>
                    <option value="no_data">Awaiting data</option>
                  </select>
                </div>
              }
            />

            {loading && stations.length === 0 ? (
              <div className="station-empty"><RefreshCw size={19} className="spin" /> Connecting to the station network…</div>
            ) : error && stations.length === 0 ? (
              <div className="station-empty">Station data is unavailable. Retry the API connection above.</div>
            ) : filteredStations.length > 0 ? (
              <div className="station-grid">
                {filteredStations.map((station) => (
                  <StationCard key={station.station_id} station={station} />
                ))}
              </div>
            ) : (
              <div className="station-empty">No stations match your search or selected status.</div>
            )}
            <div className="station-list-footer">
              <span>Showing <strong>{filteredStations.length}</strong> of <strong>{stations.length}</strong> stations</span>
              <span>Each station card reflects its latest backend snapshot.</span>
            </div>
          </section>

          <section id="redistribution" className="redistribution-section">
            <SectionHeading
              eyebrow="FIELD OPERATIONS"
              title="Redistribution desk"
              detail="Threshold-based transfer suggestions using the current station snapshot."
            />
            <div className="redistribution-layout">
              <article className="panel flow-panel">
                <div className="flow-panel-heading">
                  <div>
                    <h3>Suggested bike movements</h3>
                    <p>Surplus stations → stations needing support</p>
                  </div>
                  <span className="suggestion-count">{redistributionPlan.length} {redistributionPlan.length === 1 ? 'suggestion' : 'suggestions'}</span>
                </div>
                {redistributionPlan.length > 0 ? (
                  <div className="flow-list">
                    {redistributionPlan.map((flow, index) => (
                      <div className="flow-row" key={`${flow.from.station_id}-${flow.to.station_id}-${index}`}>
                        <div className="flow-station flow-donor">
                          <span className="flow-station-icon"><Bike size={15} /></span>
                          <span><strong>{flow.from.station_name}</strong><small>Surplus · {flow.from.available_bikes} bikes now</small></span>
                        </div>
                        <div className="flow-middle">
                          <span>{flow.bikes} {flow.bikes === 1 ? 'bike' : 'bikes'}</span>
                          <span className="flow-arrow"><ArrowRight size={17} /></span>
                        </div>
                        <div className="flow-station flow-recipient">
                          <span className="flow-station-icon"><MapPin size={15} /></span>
                          <span><strong>{flow.to.station_name}</strong><small>Shortage · {flow.to.available_bikes} bikes now</small></span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-flows">
                    <span><Check size={18} /></span>
                    <div><strong>{stations.length === 0 ? 'Station data is needed first' : 'No threshold-based transfer pairs'}</strong>
                      <p>{stations.length === 0
                        ? 'Connect to the station API to generate an operational plan.'
                        : shortageCount === 0 && surplusCount === 0
                          ? 'No reported shortages or surpluses. The network is within its operating thresholds.'
                          : 'Shortages or surpluses exist, but there is no opposite-status station to pair with.'}</p>
                    </div>
                  </div>
                )}
                <p className="flow-disclaimer">
                  Planning aid only: quantities move stations just across the API’s 20% / 80% status thresholds. No ML forecast, route optimization or transfer execution is implied.
                </p>
              </article>

              <aside className="dispatch-card">
                <div className="dispatch-mark"><Truck size={20} /></div>
                <p className="eyebrow">DISPATCH SNAPSHOT</p>
                <strong>{redistributionPlan.reduce((sum, flow) => sum + flow.bikes, 0)}</strong>
                <span>bikes in suggested transfers</span>
                <div className="dispatch-rule" />
                <div className="dispatch-rows">
                  <span><i className="legend-dot legend-low" /> Shortage stations <b>{shortageCount}</b></span>
                  <span><i className="legend-dot legend-high" /> Surplus stations <b>{surplusCount}</b></span>
                </div>
                <p className="dispatch-footnote">Review suggestions with your field team before dispatch.</p>
              </aside>
            </div>
          </section>

          <section className="model-section" aria-labelledby="model-comparison-title">
            <SectionHeading
              eyebrow="PREDICTIVE PERFORMANCE"
              title="Model comparison"
              detail="Evaluation metrics loaded from the ML engine’s saved comparison report."
              action={<span className="report-chip"><Activity size={14} /> ML ENGINE REPORT</span>}
            />
            <article className="panel model-table-panel">
              {modelsLoading ? (
                <div className="station-empty">Loading model evaluation report…</div>
              ) : modelError ? (
                <div className="model-error" role="alert">
                  <CircleHelp size={18} /><span>{modelError}</span>
                </div>
              ) : models.length > 0 ? (
                <div className="model-table-scroll">
                  <table className="model-table">
                    <thead>
                      <tr><th>Model</th><th>MAE <span>↓ lower is better</span></th><th>RMSE <span>↓ lower is better</span></th><th>MAPE <span>↓ lower is better</span></th><th>R² score <span>↑ higher is better</span></th></tr>
                    </thead>
                    <tbody>
                      {models.map((model) => (
                        <tr key={model.Model} className={model.Model === bestModel?.Model ? 'best-model-row' : ''}>
                          <td><span className="model-name"><span className="model-dot" />{model.Model}{model.Model === bestModel?.Model && <span className="best-tag">TOP RMSE</span>}</span></td>
                          <td>{Number(model.MAE).toFixed(4)}</td>
                          <td>{Number(model.RMSE).toFixed(4)}</td>
                          <td>{Number(model['MAPE (%)']).toFixed(2)}%</td>
                          <td>{Number(model.R2_Score).toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="station-empty">No model metrics are available in the ML report.</div>
              )}
              {!modelError && models.length > 0 && (
                <div className="model-table-footer">
                  <span><ShieldCheck size={15} /> Metrics generated by the ML evaluation pipeline</span>
                  <span>MAE = mean absolute error · RMSE = root mean square error · MAPE = mean absolute percentage error</span>
                </div>
              )}
            </article>
          </section>

          <footer className="dashboard-footer">
            <span>CycleFlow <i>·</i> Smart Bike Demand System</span>
            <span><span className={`live-dot${error ? ' live-dot-error' : ''}`} /> {error ? 'Backend connection needs attention' : 'Connected to the station operations API'}</span>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App
