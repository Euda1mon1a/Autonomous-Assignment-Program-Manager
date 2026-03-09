import {
  Activity,
  ArrowLeftRight,
  Beaker,
  BookOpen,
  Bug,
  Calendar,
  CalendarCheck,
  CalendarDays,
  CalendarOff,
  CheckCircle,
  ClipboardList,
  Database,
  Eye,
  FileText,
  FileUp,
  HelpCircle,
  Layers,
  LineChart,
  Network,
  Phone,
  Settings,
  Shield,
  Users,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  adminOnly?: boolean;
}

export const navItems: NavItem[] = [
  { href: "/", label: "Dashboard", icon: Calendar },
  { href: "/my-schedule", label: "My Schedule", icon: CalendarCheck },
  { href: "/schedule", label: "Schedule", icon: CalendarDays },
  { href: "/people", label: "People", icon: Users },
  { href: "/swaps", label: "Swaps", icon: ArrowLeftRight },
  { href: "/call-hub", label: "Call", icon: Phone },
  { href: "/ops", label: "Ops Hub", icon: Activity },
  { href: "/compliance", label: "Compliance", icon: CheckCircle },
  { href: "/rotations", label: "Rotations", icon: FileText },
  { href: "/activities", label: "Activities", icon: Layers },
  { href: "/procedures", label: "Procedures", icon: ClipboardList },
  { href: "/absences", label: "Absences", icon: CalendarOff },
  { href: "/analytics", label: "Analytics", icon: LineChart },
  { href: "/hub/annual-planning", label: "Annual Planning", icon: CalendarDays },
  { href: "/hub/import-export", label: "Import/Export", icon: FileUp },
  { href: "/help", label: "Help", icon: HelpCircle },
  // Core admin tools
  { href: "/admin/scheduling", label: "Lab", icon: Beaker, adminOnly: true },
  { href: "/admin/users", label: "Users", icon: Shield, adminOnly: true },
  { href: "/admin/resilience-hub", label: "Resilience", icon: Activity, adminOnly: true },
  { href: "/admin/schema", label: "Schema", icon: Database, adminOnly: true },
  { href: "/admin/block-explorer", label: "Blocks", icon: Network, adminOnly: true },
  { href: "/admin/labs", label: "Labs", icon: Beaker, adminOnly: true },
  { href: "/admin/pec", label: "PEC", icon: ClipboardList, adminOnly: true },
  { href: "/admin/board-review", label: "Board Review", icon: BookOpen, adminOnly: true },
  { href: "/admin/resilience-overseer", label: "Overseer", icon: Eye, adminOnly: true },
  { href: "/admin/debugger", label: "Debugger", icon: Bug, adminOnly: true },
  { href: "/settings", label: "Settings", icon: Settings, adminOnly: true },
];
