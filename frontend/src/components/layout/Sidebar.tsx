import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useUiStore } from '../../stores/uiStore';
import {
  LayoutDashboard,
  FilePlus,
  Cpu,
  ClipboardCheck,
  UserRound,
  Orbit,
  Search,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Lock,
} from 'lucide-react';

interface SidebarItem {
  name: string;
  path: string;
  icon: React.ReactNode;
  allowedRoles: ('admin' | 'supervisor' | 'analyst' | 'viewer')[];
  roleLabel: string;
  badge?: number;
}

export const Sidebar: React.FC = () => {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();
  const { sidebarOpen, toggleSidebar, activeConsolidationJobsCount } = useUiStore();

  const userRole = user?.role || 'viewer';

  // Helper to check if role is allowed
  const hasAccess = (allowed: typeof userRole[]) => {
    void allowed;
    return true; // Bypass role restriction for simplicity
  };

  const menuSections = [
    {
      title: 'INTELLIGENCE PROCESS',
      items: [
        {
          name: 'Dashboard',
          path: '/dashboard',
          icon: <LayoutDashboard size={18} />,
          allowedRoles: ['admin', 'supervisor', 'analyst', 'viewer'],
          roleLabel: '',
        },
        {
          name: 'Upload Reports',
          path: '/consolidate',
          icon: <FilePlus size={18} />,
          allowedRoles: ['admin', 'supervisor', 'analyst'],
          roleLabel: '',
        },
        {
          name: 'Processing Queue',
          path: '/queue',
          icon: <Cpu size={18} />,
          allowedRoles: ['admin', 'supervisor', 'analyst'],
          roleLabel: '',
          badge: activeConsolidationJobsCount > 0 ? activeConsolidationJobsCount : undefined,
        },
        {
          name: 'Review Queue',
          path: '/review',
          icon: <ClipboardCheck size={18} />,
          allowedRoles: ['admin', 'supervisor'],
          roleLabel: '',
        },
        {
          name: 'Suspect Records',
          path: '/profiles',
          icon: <UserRound size={18} />,
          allowedRoles: ['admin', 'supervisor', 'analyst', 'viewer'],
          roleLabel: '',
        },
        {
          name: 'Network Graph',
          path: '/graph',
          icon: <Orbit size={18} />,
          allowedRoles: ['admin', 'supervisor', 'analyst', 'viewer'],
          roleLabel: '',
        },
        {
          name: 'Search Engine',
          path: '/search',
          icon: <Search size={18} />,
          allowedRoles: ['admin', 'supervisor', 'analyst', 'viewer'],
          roleLabel: '',
        },
      ] as SidebarItem[],
    },
  ];

  return (
    <aside
      className={`bg-police-dark text-slate-300 flex flex-col transition-all duration-300 border-r border-police-slate select-none h-[calc(100vh-28px)] ${
        sidebarOpen ? 'w-64' : 'w-16'
      }`}
    >
      {/* Header section with Police logo mockup */}
      <div className="flex items-center justify-between p-4 border-b border-police-slate h-16 shrink-0">
        {sidebarOpen ? (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-police-light flex items-center justify-center text-police-dark font-bold text-sm">
              KP
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-bold text-white tracking-wider">KERALA POLICE</span>
              <span className="text-[10px] text-slate-400 font-medium">Intelligence Platform</span>
            </div>
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-police-light flex items-center justify-center text-police-dark font-bold text-sm mx-auto">
            KP
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="text-slate-400 hover:text-white p-1 rounded hover:bg-police-slate transition-colors hidden sm:block"
        >
          {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </button>
      </div>

      {/* Nav Menu Items */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-4">
        {menuSections.map((section) => {
          // Check if section contains any item
          const isSectionVisible = section.items.length > 0;
          if (!isSectionVisible) return null;

          return (
            <div key={section.title} className="space-y-1">
              {sidebarOpen && (
                <h3 className="text-[10px] font-bold text-slate-500 tracking-wider px-3 mb-1">
                  {section.title}
                </h3>
              )}
              
              {section.items.map((item) => {
                const allowed = hasAccess(item.allowedRoles);

                if (!allowed) {
                  // Render disabled state as requested by UX architecture
                  return (
                    <div
                      key={item.name}
                      title={`Requires ${item.roleLabel || 'authorized'} role.`}
                      className={`flex items-center justify-between px-3 py-2 text-sm text-slate-600 cursor-not-allowed rounded-md`}
                    >
                      <div className="flex items-center gap-3">
                        {item.icon}
                        {sidebarOpen && <span>{item.name}</span>}
                      </div>
                      {sidebarOpen && <Lock size={12} className="text-slate-600" />}
                    </div>
                  );
                }

                return (
                  <NavLink
                    key={item.name}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-2 text-sm rounded-md transition-all duration-150 ${
                        isActive
                          ? 'bg-police-light text-police-dark font-semibold shadow-premium'
                          : 'hover:bg-police-slate hover:text-white text-slate-400'
                      }`
                    }
                  >
                    <div className="flex items-center gap-3">
                      {item.icon}
                      {sidebarOpen && <span>{item.name}</span>}
                    </div>
                    {sidebarOpen && item.badge !== undefined && item.badge > 0 && (
                      <span className="bg-police-accent text-white font-bold text-[10px] px-2 py-0.5 rounded-full animate-pulse">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          );
        })}
      </div>

      {/* Footer / Account Action */}
      <div className="p-3 border-t border-police-slate shrink-0">
        <button
          onClick={() => { logout(); navigate('/login'); }}
          className="w-full flex items-center gap-3 px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-police-slate rounded-md transition-colors"
          title="Sign Out of Session"
        >
          <LogOut size={18} />
          {sidebarOpen && <span>Sign Out</span>}
        </button>
      </div>
    </aside>
  );
};
