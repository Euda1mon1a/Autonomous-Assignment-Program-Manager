'use client'

import { Printer, HelpCircle, Book, MessageCircle, FileText } from 'lucide-react'

export default function HelpPage() {
  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 print:px-0 print:py-0 print:max-w-none">
      {/* Header - hidden in print */}
      <div className="flex justify-between items-center mb-8 print:hidden">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Help & Reference</h1>
          <p className="text-gray-600">Quick reference, glossary, and frequently asked questions</p>
        </div>
        <button
          onClick={handlePrint}
          className="btn-primary flex items-center gap-2"
        >
          <Printer className="w-4 h-4" />
          Print / Save PDF
        </button>
      </div>

      {/* Print Header - only visible in print */}
      <div className="hidden print:block print:mb-6 print:text-center print:border-b print:pb-4">
        <h1 className="text-2xl font-bold">Residency Scheduler Quick Reference Guide</h1>
        <p className="text-sm text-gray-600 mt-1">Print this page or save as PDF for offline reference</p>
      </div>

      {/* Quick Reference Card */}
      <section className="mb-10 print:mb-6 print:break-after-page">
        <div className="flex items-center gap-2 mb-4 print:mb-3">
          <FileText className="w-6 h-6 text-blue-600 print:hidden" />
          <h2 className="text-xl font-bold text-gray-900 print:text-lg">Quick Reference Card</h2>
        </div>

        <div className="grid md:grid-cols-2 gap-4 print:gap-3 print:grid-cols-2">
          {/* Common Tasks */}
          <div className="card print:p-3 print:shadow-none print:border">
            <h3 className="font-semibold text-blue-800 mb-3 print:mb-2 print:text-sm">Common Tasks</h3>
            <div className="space-y-2 text-sm print:text-xs print:space-y-1">
              <div className="flex justify-between">
                <span>Generate a schedule</span>
                <span className="text-gray-500">Dashboard → Generate Schedule</span>
              </div>
              <div className="flex justify-between">
                <span>Add a new resident</span>
                <span className="text-gray-500">People → Add Person</span>
              </div>
              <div className="flex justify-between">
                <span>Record time off</span>
                <span className="text-gray-500">Absences → Add Absence</span>
              </div>
              <div className="flex justify-between">
                <span>Check compliance</span>
                <span className="text-gray-500">Compliance page</span>
              </div>
              <div className="flex justify-between">
                <span>Export to Excel</span>
                <span className="text-gray-500">Dashboard → Export Excel</span>
              </div>
              <div className="flex justify-between">
                <span>Create rotation type</span>
                <span className="text-gray-500">Templates → New Template</span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div className="card print:p-3 print:shadow-none print:border">
            <h3 className="font-semibold text-blue-800 mb-3 print:mb-2 print:text-sm">Navigation Guide</h3>
            <div className="space-y-2 text-sm print:text-xs print:space-y-1">
              <div><strong>Dashboard</strong> - Home page, overview, quick actions</div>
              <div><strong>People</strong> - Manage residents and faculty</div>
              <div><strong>Templates</strong> - Rotation types and rules</div>
              <div><strong>Absences</strong> - Vacation, deployment, sick leave</div>
              <div><strong>Compliance</strong> - ACGME rule monitoring</div>
              <div><strong>Settings</strong> - System config (Admin only)</div>
            </div>
          </div>

          {/* Absence Types */}
          <div className="card print:p-3 print:shadow-none print:border">
            <h3 className="font-semibold text-green-800 mb-3 print:mb-2 print:text-sm">Absence Types</h3>
            <div className="space-y-2 text-sm print:text-xs print:space-y-1">
              <div><strong>Vacation</strong> - Planned annual leave</div>
              <div><strong>Medical</strong> - Sick days, appointments</div>
              <div><strong>Deployment</strong> - Military active duty</div>
              <div><strong>TDY</strong> - Temporary duty assignment</div>
              <div><strong>Conference</strong> - CME, medical meetings</div>
              <div><strong>Family Emergency</strong> - Personal matters</div>
            </div>
          </div>

          {/* User Roles */}
          <div className="card print:p-3 print:shadow-none print:border">
            <h3 className="font-semibold text-purple-800 mb-3 print:mb-2 print:text-sm">User Roles</h3>
            <div className="space-y-2 text-sm print:text-xs print:space-y-1">
              <div><strong>Admin</strong> - Full access, can change settings</div>
              <div><strong>Coordinator</strong> - Manage schedules, people, absences</div>
              <div><strong>Faculty</strong> - View only access</div>
            </div>
            <div className="mt-3 pt-3 border-t text-xs text-gray-500 print:mt-2 print:pt-2">
              Can&apos;t see Settings? You need Admin role.
            </div>
          </div>

          {/* ACGME Rules */}
          <div className="card print:p-3 print:shadow-none print:border">
            <h3 className="font-semibold text-red-800 mb-3 print:mb-2 print:text-sm">ACGME Compliance Rules</h3>
            <div className="space-y-2 text-sm print:text-xs print:space-y-1">
              <div><strong>80-Hour Rule</strong> - Max 80 hrs/week (4-week avg)</div>
              <div><strong>1-in-7 Rule</strong> - One day off every 7 days</div>
              <div><strong>PGY-1 Supervision</strong> - 1 faculty per 2 residents</div>
              <div><strong>PGY-2/3 Supervision</strong> - 1 faculty per 4 residents</div>
            </div>
          </div>

          {/* Export Options */}
          <div className="card print:p-3 print:shadow-none print:border">
            <h3 className="font-semibold text-amber-800 mb-3 print:mb-2 print:text-sm">Export Options</h3>
            <div className="space-y-2 text-sm print:text-xs print:space-y-1">
              <div><strong>Excel (.xlsx)</strong> - Dashboard → Export Excel</div>
              <div><strong>CSV</strong> - People/Absences → Export dropdown</div>
              <div><strong>JSON</strong> - People/Absences → Export dropdown</div>
            </div>
            <div className="mt-3 pt-3 border-t text-xs text-gray-500 print:mt-2 print:pt-2">
              Excel export uses the legacy 4-week block format
            </div>
          </div>
        </div>
      </section>

      {/* Glossary */}
      <section className="mb-10 print:mb-6 print:break-after-page">
        <div className="flex items-center gap-2 mb-4 print:mb-3">
          <Book className="w-6 h-6 text-green-600 print:hidden" />
          <h2 className="text-xl font-bold text-gray-900 print:text-lg">Glossary of Terms</h2>
        </div>

        <div className="card print:p-3 print:shadow-none print:border">
          <div className="grid md:grid-cols-2 gap-x-8 gap-y-3 print:gap-x-4 print:gap-y-2 print:grid-cols-2">
            <GlossaryItem
              term="ACGME"
              definition="Accreditation Council for Graduate Medical Education - sets residency training standards"
            />
            <GlossaryItem
              term="PGY"
              definition="Post-Graduate Year - PGY-1 is first year, PGY-2 is second year, etc."
            />
            <GlossaryItem
              term="Block"
              definition="A scheduling period, typically 4 weeks (28 days)"
            />
            <GlossaryItem
              term="Rotation"
              definition="A clinical assignment (e.g., Inpatient, Clinic, ICU)"
            />
            <GlossaryItem
              term="TDY"
              definition="Temporary Duty - military assignment away from home station"
            />
            <GlossaryItem
              term="Deployment"
              definition="Military active duty assignment, typically overseas"
            />
            <GlossaryItem
              term="Template"
              definition="A reusable rotation definition with rules and constraints"
            />
            <GlossaryItem
              term="Supervision Ratio"
              definition="Required number of faculty per resident (e.g., 1:2 means 1 faculty per 2 residents)"
            />
            <GlossaryItem
              term="Coverage Rate"
              definition="Percentage of required positions that are filled"
            />
            <GlossaryItem
              term="Violation"
              definition="When a schedule breaks an ACGME rule"
            />
            <GlossaryItem
              term="Academic Year"
              definition="Typically July 1 to June 30 for residency programs"
            />
            <GlossaryItem
              term="CME"
              definition="Continuing Medical Education - required ongoing training"
            />
            <GlossaryItem
              term="Greedy Algorithm"
              definition="Fast scheduling method that fills slots one at a time"
            />
            <GlossaryItem
              term="CP-SAT"
              definition="Constraint Programming - slower but finds optimal schedules"
            />
            <GlossaryItem
              term="AM/PM"
              definition="Morning and afternoon sessions in the daily schedule"
            />
            <GlossaryItem
              term="Faculty"
              definition="Attending physicians who supervise residents"
            />
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="mb-10 print:mb-6">
        <div className="flex items-center gap-2 mb-4 print:mb-3">
          <MessageCircle className="w-6 h-6 text-purple-600 print:hidden" />
          <h2 className="text-xl font-bold text-gray-900 print:text-lg">Frequently Asked Questions</h2>
        </div>

        <div className="space-y-4 print:space-y-3">
          <FAQItem
            question="Why can't I see the Settings page?"
            answer="Settings is only available to Admin users. If you need to change settings, contact your program administrator."
          />
          <FAQItem
            question="How do I reset my password?"
            answer="Contact your program administrator to reset your password. They can update it in the system."
          />
          <FAQItem
            question="Why is the schedule showing compliance violations?"
            answer="Violations appear when the schedule breaks ACGME rules. Check the Compliance page to see which rules are broken and for which residents. You may need to adjust the schedule to reduce hours or add days off."
          />
          <FAQItem
            question="What's the difference between Deployment and TDY?"
            answer="Deployment is typically a longer military assignment (often overseas). TDY (Temporary Duty) is a shorter assignment, usually for training or temporary work at another location."
          />
          <FAQItem
            question="How do I add a new resident at the start of the year?"
            answer="Go to People → Add Person. Select 'Resident' as the type, set PGY level to 1 for interns, and fill in their information."
          />
          <FAQItem
            question="How do I update a resident's PGY level?"
            answer="Go to People, find the resident, click Edit, and change their PGY level. Do this at the start of each academic year for advancing residents."
          />
          <FAQItem
            question="What does 'Coverage Rate' mean?"
            answer="Coverage rate shows what percentage of required positions are filled. 100% means all slots are covered. Lower percentages indicate gaps in the schedule that need to be filled."
          />
          <FAQItem
            question="Which scheduling algorithm should I use?"
            answer="Start with 'Greedy' for quick results. If you're getting many violations, try 'Min Conflicts' for better optimization. Use 'CP-SAT' when you need the best possible schedule and have time to wait."
          />
          <FAQItem
            question="How do I print the schedule for distribution?"
            answer="From the Dashboard, click 'Export Excel'. This downloads a formatted spreadsheet you can print or email to residents and faculty."
          />
          <FAQItem
            question="Can I use this on my phone?"
            answer="Yes, the application works on mobile devices. The navigation menu collapses into a hamburger menu on smaller screens. For best experience, use a tablet or computer for complex tasks."
          />
          <FAQItem
            question="How far in advance can I generate schedules?"
            answer="You can generate schedules for any date range. Most programs generate one block (4 weeks) at a time, but you can do an entire month or longer if needed."
          />
          <FAQItem
            question="What happens if I delete a person who has scheduled assignments?"
            answer="Their assignments will be affected. It's best to first remove or reassign their scheduled slots, then delete the person. The system will warn you before deletion."
          />
          <FAQItem
            question="How do I handle a last-minute sick call?"
            answer="Add the absence in the Absences page with today's date. Then check the Dashboard to see coverage impact. You may need to manually reassign or find coverage."
          />
          <FAQItem
            question="Can multiple people use the system at the same time?"
            answer="Yes, multiple users can be logged in simultaneously. Changes are saved to the database and will be visible to other users when they refresh."
          />
        </div>
      </section>

      {/* Print Footer */}
      <div className="hidden print:block print:mt-8 print:pt-4 print:border-t print:text-center print:text-xs print:text-gray-500">
        <p>Residency Scheduler Quick Reference Guide</p>
        <p>For additional help, contact your program administrator</p>
      </div>
    </div>
  )
}

function GlossaryItem({ term, definition }: { term: string; definition: string }) {
  return (
    <div className="text-sm print:text-xs">
      <span className="font-semibold text-gray-900">{term}</span>
      <span className="text-gray-500"> — </span>
      <span className="text-gray-700">{definition}</span>
    </div>
  )
}

function FAQItem({ question, answer }: { question: string; answer: string }) {
  return (
    <div className="card print:p-3 print:shadow-none print:border">
      <h3 className="font-semibold text-gray-900 mb-2 print:mb-1 print:text-sm flex items-start gap-2">
        <HelpCircle className="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5 print:hidden" />
        <span>{question}</span>
      </h3>
      <p className="text-gray-600 text-sm print:text-xs print:ml-0 ml-7">{answer}</p>
    </div>
  )
}
