import { Link, useLocation } from 'react-router-dom'
import { FileText, FolderOpen, Tag } from 'lucide-react'
import clsx from 'clsx'

export function Navbar() {
  const { pathname } = useLocation()

  const links = [
    { to: '/', label: 'Proyectos', icon: FolderOpen },
  ]

  return (
    <nav className="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-6 shadow-sm">
      <div className="flex items-center gap-2 font-bold text-slate-800 text-lg mr-6">
        <FileText className="text-blue-600" size={22} />
        <span>Etiquetado Manuscritos</span>
      </div>
      {links.map(({ to, label, icon: Icon }) => (
        <Link
          key={to}
          to={to}
          className={clsx(
            'flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-md transition-colors',
            pathname === to
              ? 'bg-blue-50 text-blue-700'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          )}
        >
          <Icon size={15} />
          {label}
        </Link>
      ))}
    </nav>
  )
}
