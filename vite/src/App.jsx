import { useCallback, useEffect, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  ArrowDownUp,
  Bike,
  ChevronDown,
  CircleHelp,
  LayoutDashboard,
  MapPin,
  Menu,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Truck,
  X,
} from 'lucide-react'
import { getStationStatus } from './services/api'

const statusStyles = {
  shortage: 'bg-red-50 text-red-700 ring-red-200',
  balanced: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  surplus: 'bg-amber-50 text-amber-700 ring-amber-200',
  no_data: 'bg-slate-100 text-slate-600 ring-slate-200',
}

const statusLabels = {
  shortage: 'Shortage',
  balanced: 'Balanced',
  surplus: 'Surplus',
  no_data: 'No data',
}

const SIDEBAR_KEY = 'cycleflow.sidebarOpen'

function getInitialSidebarState() {
  // On phones/tablets the sidebar starts hidden (it opens as a drawer).
  if (typeof window !== 'undefined' && window.innerWidth < 1024) return false
  try {
    const saved = localStorage.getItem(SIDEBAR_KEY)
    return saved === null ? true : saved === 'true'
  } catch {
    return true
  }
}

function StatCard({ title, value, subtitle, icon: Icon, color }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
            {value}
          </p>
        </div>
        <div className={`rounded-xl p-3 ${color}`}>
          <Icon size={22} />
        </div>
      </div>
      <p className="mt-3 text-xs text-slate-500">{subtitle}</p>
    </div>
  )
}

function NavItem({ icon: Icon, label, active = false }) {
  return (
    <div
      className={`flex items-center gap-3 rounded-xl px-3 py-3 ${
        active
          ? 'bg-emerald-400/15 font-medium text-emerald-300'
          : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
      }`}
    >
      <Icon size={19} />
      {label}
    </div>
  )
}

function App() {
  const [stations, setStations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [lastUpdated, setLastUpdated] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(getInitialSidebarState)

  const toggleSidebar = useCallback(() => {
    setSidebarOpen((open) => {
      const next = !open
      try {
        // Only remember the choice made on desktop-sized screens.
        if (window.innerWidth >= 1024) {
          localStorage.setItem(SIDEBAR_KEY, String(next))
        }
      } catch {
        /* storage unavailable, ignore */
      }
      return next
    })
  }, [])

  // Close the drawer with the Escape key (mobile).
  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === 'Escape' && window.innerWidth < 1024) {
        setSidebarOpen(false)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const loadStations = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const data = await getStationStatus()
      setStations(data)
      setLastUpdated(new Date())
    } catch (err) {
      setError(err.message || 'Could not connect to the backend.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadStations()
  }, [loadStations])

  const knownStations = stations.filter(
    (station) => station.available_bikes !== null
  )

  const totalBikes = knownStations.reduce(
    (sum, station) => sum + station.available_bikes,
    0
  )

  const shortageCount = stations.filter(
    (station) => station.status === 'shortage'
  ).length

  const surplusCount = stations.filter(
    (station) => station.status === 'surplus'
  ).length

  const filteredStations = stations.filter((station) => {
    const matchesSearch =
      station.station_name.toLowerCase().includes(search.toLowerCase()) ||
      station.station_id.toLowerCase().includes(search.toLowerCase())

    const matchesFilter = filter === 'all' || station.status === filter

    return matchesSearch && matchesFilter
  })

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {/* Backdrop: only on small screens while the drawer is open */}
      <div
        onClick={() => setSidebarOpen(false)}
        aria-hidden="true"
        className={`fixed inset-0 z-20 bg-slate-950/50 transition-opacity duration-300 lg:hidden ${
          sidebarOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
      />

      <aside
        aria-hidden={!sidebarOpen}
        className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-slate-950 text-white transition-transform duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-20 items-center justify-between gap-3 border-b border-white/10 px-6">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-400 p-2 text-slate-950">
              <Bike size={25} />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">CycleFlow</h1>
              <p className="text-xs text-slate-400">SMART BIKE SYSTEM</p>
            </div>
          </div>
          <button
            onClick={toggleSidebar}
            aria-label="Hide sidebar"
            title="Hide sidebar"
            className="rounded-lg p-1.5 text-slate-400 transition hover:bg-white/10 hover:text-white"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-4 py-7">
          <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
            Workspace
          </p>
          <nav className="space-y-1">
            <NavItem icon={LayoutDashboard} label="Dashboard" active />
            <NavItem icon={MapPin} label="Stations" />
            <NavItem icon={Activity} label="Demand Forecasting" />
            <NavItem icon={Truck} label="Redistribution" />
            <NavItem icon={ArrowDownUp} label="History & Reports" />
          </nav>
        </div>

        <div className="mt-auto border-t border-white/10 p-4">
          <div className="flex items-center gap-3 rounded-xl bg-white/5 p-3">
            <ShieldCheck className="text-emerald-300" size={22} />
            <div>
              <p className="text-sm font-medium">System status</p>
              <p className="text-xs text-slate-400">API connection checked on refresh</p>
            </div>
          </div>
          <div className="mt-2 flex items-center gap-3 px-3 py-3 text-sm text-slate-400">
            <Settings size={18} />
            Settings
          </div>
        </div>
      </aside>

      <main
        className={`transition-[margin] duration-300 ease-in-out ${
          sidebarOpen ? 'lg:ml-64' : 'lg:ml-0'
        }`}
      >
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-white px-5 py-5 sm:px-8">
          <div className="flex items-center gap-4">
            <button
              onClick={toggleSidebar}
              aria-label={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
              aria-expanded={sidebarOpen}
              title={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
              className="rounded-xl border border-slate-200 p-2.5 text-slate-600 transition hover:bg-slate-100"
            >
              <Menu size={20} />
            </button>
            <div>
              <p className="text-sm text-slate-500">Operations / Overview</p>
              <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">
                Operations Dashboard
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-semibold text-slate-800">Fleet operator</p>
              <p className="text-xs text-slate-500">Administrator</p>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-200 font-bold text-slate-700">
              FO
            </div>
            <ChevronDown size={17} className="text-slate-500" />
          </div>
        </header>

        <div className="space-y-7 p-5 sm:p-8">
          <section className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">
                Fleet overview
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Monitor station availability and identify where action is needed.
              </p>
            </div>
            <button
              onClick={loadStations}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-50"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
              Refresh data
            </button>
          </section>

          {error && (
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <span>{error}. Check that FastAPI is running on port 8000.</span>
              <button onClick={loadStations} className="font-semibold underline">
                Try again
              </button>
            </div>
          )}

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              title="Total stations"
              value={loading && stations.length === 0 ? '—' : stations.length}
              subtitle="Registered bicycle stations"
              icon={MapPin}
              color="bg-blue-50 text-blue-700"
            />
            <StatCard
              title="Available bikes"
              value={loading && stations.length === 0 ? '—' : totalBikes}
              subtitle={`Recorded at ${knownStations.length} station(s)`}
              icon={Bike}
              color="bg-emerald-50 text-emerald-700"
            />
            <StatCard
              title="Shortage stations"
              value={shortageCount}
              subtitle="Stations needing more bikes"
              icon={AlertTriangle}
              color="bg-red-50 text-red-700"
            />
            <StatCard
              title="Surplus stations"
              value={surplusCount}
              subtitle="Stations with extra bikes"
              icon={Truck}
              color="bg-amber-50 text-amber-700"
            />
          </section>

          <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 p-5">
              <div>
                <h3 className="font-semibold text-slate-900">Station status</h3>
                <p className="mt-1 text-sm text-slate-500">
                  Latest recorded availability for each station
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <div className="relative">
                  <Search
                    size={16}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                  />
                  <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search stations..."
                    className="w-52 rounded-xl border border-slate-200 py-2 pl-9 pr-3 text-sm outline-none focus:border-emerald-500"
                  />
                </div>
                <select
                  value={filter}
                  onChange={(event) => setFilter(event.target.value)}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-500"
                >
                  <option value="all">Show All</option>
                  <option value="shortage">Shortage</option>
                  <option value="balanced">Balanced</option>
                  <option value="surplus">Surplus</option>
                  <option value="no_data">No data</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-5 py-4 font-semibold">Station</th>
                    <th className="px-5 py-4 font-semibold">Capacity</th>
                    <th className="px-5 py-4 font-semibold">Available Bikes</th>
                    <th className="px-5 py-4 font-semibold">Availability</th>
                    <th className="px-5 py-4 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {!loading && !error && filteredStations.map((station) => (
                    <tr key={station.station_id} className="transition hover:bg-slate-50">
                      <td className="px-5 py-4">
                        <p className="font-semibold text-slate-800">
                          {station.station_name}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">
                          {station.station_id}
                        </p>
                      </td>
                      <td className="px-5 py-4 text-slate-600">
                        {station.capacity}
                      </td>
                      <td className="px-5 py-4 font-medium text-slate-800">
                        {station.available_bikes ?? '—'}
                        <span className="font-normal text-slate-400">
                          {' '}/ {station.capacity}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        {station.bike_percentage === null ? (
                          <span className="text-slate-400">No snapshot</span>
                        ) : (
                          <div className="flex items-center gap-3">
                            <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-100">
                              <div
                                className="h-full rounded-full bg-emerald-500"
                                style={{
                                  width: `${Math.min(station.bike_percentage, 100)}%`,
                                }}
                              />
                            </div>
                            <span className="text-slate-600">
                              {station.bike_percentage}%
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${
                            statusStyles[station.status] || statusStyles.no_data
                          }`}
                        >
                          {statusLabels[station.status] || station.status}
                        </span>
                      </td>
                    </tr>
                  ))}

                  {loading && (
                    <tr>
                      <td colSpan="5" className="px-5 py-12 text-center text-slate-500">
                        Loading station data...
                      </td>
                    </tr>
                  )}

                  {!loading && !error && filteredStations.length === 0 && (
                    <tr>
                      <td colSpan="5" className="px-5 py-12 text-center text-slate-500">
                        No stations match your search.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-200 px-5 py-4 text-xs text-slate-500">
              <span>
                Showing {filteredStations.length} of {stations.length} stations
              </span>
              <span>
                {lastUpdated
                  ? `Last refreshed at ${lastUpdated.toLocaleTimeString()}`
                  : 'Waiting for station data'}
              </span>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-2">
            <div className="flex gap-4 rounded-2xl border border-slate-200 bg-white p-5">
              <div className="h-fit rounded-xl bg-blue-50 p-3 text-blue-700">
                <CircleHelp size={22} />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Data coverage</h3>
                <p className="mt-1 text-sm leading-6 text-slate-500">
                  {knownStations.length} of {stations.length} stations currently have
                  recorded availability. Stations without snapshots are marked
                  “No data” and are excluded from the bike total.
                </p>
              </div>
            </div>
            <div className="flex gap-4 rounded-2xl border border-slate-200 bg-white p-5">
              <div className="h-fit rounded-xl bg-emerald-50 p-3 text-emerald-700">
                <Truck size={22} />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">
                  Redistribution planning
                </h3>
                <p className="mt-1 text-sm leading-6 text-slate-500">
                  Recommendations will appear here after we implement the
                  redistribution API. No bike transfers are performed by this
                  dashboard yet.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

export default App
