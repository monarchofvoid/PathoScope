'use client';

import { useAuth } from '../../../contexts/AuthContext';
import DashboardLayout from '../../../components/DashboardLayout';
import InfectionCaseForm from '../../../components/InfectionCaseForm';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function CasesPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [showForm, setShowForm] = useState(false);
  const [editingCase, setEditingCase] = useState(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const handleCaseSuccess = (caseData: any) => {
    setShowForm(false);
    setEditingCase(null);
    // In a real app, you would refresh the cases list or redirect
    console.log('Case created/updated:', caseData);
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingCase(null);
  };

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Infection Cases</h1>
            <p className="text-gray-600">Manage verified infection cases and TEK verification tokens</p>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            New Case
          </button>
        </div>

        {(showForm || editingCase) && (
          <div className="mb-6">
            <InfectionCaseForm
              onSuccess={handleCaseSuccess}
              onCancel={handleCancel}
              initialData={editingCase}
            />
          </div>
        )}

        {/* Cases List Placeholder */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Cases</h3>
          <div className="text-center py-8 text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No cases yet</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new infection case.</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}