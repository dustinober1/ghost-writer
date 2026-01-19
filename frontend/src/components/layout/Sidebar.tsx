import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, User, PenTool, History, Menu, X, Layers } from 'lucide-react';
import { useState } from 'react';
import { cn } from '../../utils/cn';
import Button from '../ui/Button';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/analyze', label: 'Text Analysis', icon: FileText },
  { path: '/batch', label: 'Batch Analysis', icon: Layers },
  { path: '/history', label: 'History', icon: History },
  { path: '/profile', label: 'Profile & Fingerprint', icon: User },
  { path: '/rewrite', label: 'Style Rewriting', icon: PenTool },
];

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-16 left-0 right-0 z-30 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsOpen(!isOpen)}
          className="gap-2"
        >
          {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          <span>Menu</span>
        </Button>
      </div>

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:sticky top-16 lg:top-16 left-0 z-30 h-[calc(100vh-4rem)] w-64 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 transition-transform duration-300',
          'lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                    'hover:bg-gray-100 dark:hover:bg-gray-800',
                    isActive
                      ? 'bg-primary-50 dark:bg-primary-950/20 text-primary-700 dark:text-primary-400'
                      : 'text-gray-700 dark:text-gray-300'
                  )
                }
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
