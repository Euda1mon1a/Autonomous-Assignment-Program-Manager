'use client'

interface Assignment {
  id: string
  activity: string
  abbreviation: string
  role: string
}

interface DayCellProps {
  date: Date
  amAssignment?: Assignment
  pmAssignment?: Assignment
}

// Activity type to color mapping
const activityColors: Record<string, string> = {
  clinic: 'bg-clinic-light text-clinic-dark',
  inpatient: 'bg-inpatient-light text-inpatient-dark',
  call: 'bg-call-light text-call-dark',
  leave: 'bg-leave-light text-leave-dark',
  conference: 'bg-gray-100 text-gray-700',
  default: 'bg-blue-50 text-blue-700',
}

function getActivityColor(activity: string): string {
  const activityLower = activity.toLowerCase()

  for (const [key, color] of Object.entries(activityColors)) {
    if (activityLower.includes(key)) {
      return color
    }
  }

  return activityColors.default
}

export function DayCell({ date, amAssignment, pmAssignment }: DayCellProps) {
  const isWeekend = date.getDay() === 0 || date.getDay() === 6

  // If both AM and PM are the same activity, show as one
  const isSameActivity =
    amAssignment &&
    pmAssignment &&
    amAssignment.activity === pmAssignment.activity

  if (!amAssignment && !pmAssignment) {
    return (
      <div
        className={`schedule-cell ${
          isWeekend ? 'bg-gray-50' : 'bg-white'
        }`}
      >
        <div className="text-center text-gray-300 text-sm">-</div>
      </div>
    )
  }

  if (isSameActivity) {
    return (
      <div
        className={`schedule-cell ${getActivityColor(amAssignment.activity)}`}
        title={amAssignment.activity}
      >
        <div className="text-center">
          <div className="font-medium">{amAssignment.abbreviation}</div>
          <div className="text-xs opacity-75">All day</div>
        </div>
      </div>
    )
  }

  return (
    <div className={`schedule-cell ${isWeekend ? 'bg-gray-50' : 'bg-white'}`}>
      {/* AM */}
      <div
        className={`rounded px-1 py-0.5 mb-1 text-xs ${
          amAssignment ? getActivityColor(amAssignment.activity) : ''
        }`}
        title={amAssignment?.activity}
      >
        {amAssignment ? (
          <>
            <span className="font-medium">{amAssignment.abbreviation}</span>
            <span className="ml-1 opacity-75">AM</span>
          </>
        ) : (
          <span className="text-gray-300">-</span>
        )}
      </div>

      {/* PM */}
      <div
        className={`rounded px-1 py-0.5 text-xs ${
          pmAssignment ? getActivityColor(pmAssignment.activity) : ''
        }`}
        title={pmAssignment?.activity}
      >
        {pmAssignment ? (
          <>
            <span className="font-medium">{pmAssignment.abbreviation}</span>
            <span className="ml-1 opacity-75">PM</span>
          </>
        ) : (
          <span className="text-gray-300">-</span>
        )}
      </div>
    </div>
  )
}
