import { CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { formatDomainLabel } from './domainUtils';

interface ComplianceBadgeProps {
  domain: string;
  status: 'compliant' | 'pending' | 'at-risk';
  showLabel?: boolean;
}

export function ComplianceBadge({ domain, status, showLabel = true }: ComplianceBadgeProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'compliant':
        return 'bg-green-100 border-green-300 text-green-700';
      case 'pending':
        return 'bg-yellow-100 border-yellow-300 text-yellow-700';
      case 'at-risk':
        return 'bg-red-100 border-red-300 text-red-700';
      default:
        return 'bg-gray-100 border-gray-300 text-gray-700';
    }
  };

  const getIcon = () => {
    switch (status) {
      case 'compliant':
        return <CheckCircle2 className="w-4 h-4" />;
      case 'pending':
        return <Clock className="w-4 h-4" />;
      case 'at-risk':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return null;
    }
  };

  return (
    <div className={`inline-flex flex-col items-center p-3 rounded-xl border-2 ${getStatusColor()} transition-all hover:shadow-md`}>
      <div className="flex items-center space-x-2 mb-1">
        {getIcon()}
        <span className="font-bold text-sm">{formatDomainLabel(domain)}</span>
      </div>
      {showLabel && (
        <span className="text-xs font-semibold capitalize">
          {status === 'at-risk' ? 'At Risk' : status}
        </span>
      )}
    </div>
  );
}
