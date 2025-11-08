'use client';

import React, { useState } from 'react';
import { apiService } from '../services/api';
import { InfectionCaseCreate, PathogenType, TestType } from '../../../shared/types';

interface InfectionCaseFormProps {
  onSuccess?: (caseData: any) => void;
  onCancel?: () => void;
  initialData?: Partial<InfectionCaseCreate>;
}

const pathogenLookbackDays: Record<PathogenType, number> = {
  [PathogenType.MDR_TB]: 21,
  [PathogenType.CRE]: 14,
  [PathogenType.MRSA]: 14,
  [PathogenType.VRE]: 14,
  [PathogenType.CANDIDA_AURIS]: 30,
  [PathogenType.OTHER]: 14,
};

export default function InfectionCaseForm({ onSuccess, onCancel, initialData }: InfectionCaseFormProps) {
  const [formData, setFormData] = useState<InfectionCaseCreate>({
    patient_identifier: initialData?.patient_identifier || '',
    staff_identifier: initialData?.staff_identifier || '',
    pathogen_type: initialData?.pathogen_type || PathogenType.MRSA,
    test_type: initialData?.test_type || TestType.PCR,
    specimen_collection_date: initialData?.specimen_collection_date || '',
    symptom_onset_date: initialData?.symptom_onset_date || '',
    tek_lookback_days: initialData?.tek_lookback_days || 14,
    notes: initialData?.notes || '',
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));

    // Auto-adjust lookback days based on pathogen type
    if (name === 'pathogen_type') {
      const pathogen = value as PathogenType;
      setFormData(prev => ({
        ...prev,
        pathogen_type: pathogen,
        tek_lookback_days: pathogenLookbackDays[pathogen],
      }));
    }

    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.patient_identifier.trim()) {
      errors.patient_identifier = 'Patient identifier is required';
    }

    if (!formData.specimen_collection_date) {
      errors.specimen_collection_date = 'Specimen collection date is required';
    }

    if (formData.symptom_onset_date && formData.specimen_collection_date) {
      const symptomDate = new Date(formData.symptom_onset_date);
      const specimenDate = new Date(formData.specimen_collection_date);
      if (symptomDate > specimenDate) {
        errors.symptom_onset_date = 'Symptom onset cannot be after specimen collection date';
      }
    }

    if (formData.tek_lookback_days < 1 || formData.tek_lookback_days > 30) {
      errors.tek_lookback_days = 'Lookback days must be between 1 and 30';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const caseData = {
        ...formData,
        specimen_collection_date: new Date(formData.specimen_collection_date).toISOString(),
        symptom_onset_date: formData.symptom_onset_date ? new Date(formData.symptom_onset_date).toISOString() : undefined,
      };

      const createdCase = await apiService.createInfectionCase(caseData);
      onSuccess?.(createdCase);
    } catch (err) {
      console.error('Failed to create infection case:', err);
      setError(err instanceof Error ? err.message : 'Failed to create infection case');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDateTimeLocal = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toISOString().slice(0, 16);
  };

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
          {initialData ? 'Edit Infection Case' : 'New Infection Case'}
        </h3>

        {error && (
          <div className="rounded-md bg-red-50 p-4 mb-4">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            {/* Patient Identifier */}
            <div>
              <label htmlFor="patient_identifier" className="block text-sm font-medium text-gray-700">
                Patient Identifier *
              </label>
              <input
                type="text"
                id="patient_identifier"
                name="patient_identifier"
                required
                className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  fieldErrors.patient_identifier ? 'border-red-500' : ''
                }`}
                value={formData.patient_identifier}
                onChange={handleInputChange}
                disabled={isLoading}
              />
              {fieldErrors.patient_identifier && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.patient_identifier}</p>
              )}
            </div>

            {/* Staff Identifier */}
            <div>
              <label htmlFor="staff_identifier" className="block text-sm font-medium text-gray-700">
                Staff Identifier (if applicable)
              </label>
              <input
                type="text"
                id="staff_identifier"
                name="staff_identifier"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                value={formData.staff_identifier || ''}
                onChange={handleInputChange}
                disabled={isLoading}
              />
            </div>

            {/* Pathogen Type */}
            <div>
              <label htmlFor="pathogen_type" className="block text-sm font-medium text-gray-700">
                Pathogen Type *
              </label>
              <select
                id="pathogen_type"
                name="pathogen_type"
                required
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                value={formData.pathogen_type}
                onChange={handleInputChange}
                disabled={isLoading}
              >
                <option value={PathogenType.MDR_TB}>MDR Tuberculosis</option>
                <option value={PathogenType.CRE}>Carbapenem-Resistant Enterobacteriaceae (CRE)</option>
                <option value={PathogenType.MRSA}>Methicillin-Resistant Staphylococcus aureus (MRSA)</option>
                <option value={PathogenType.VRE}>Vancomycin-Resistant Enterococci (VRE)</option>
                <option value={PathogenType.CANDIDA_AURIS}>Candida auris</option>
                <option value={PathogenType.OTHER}>Other</option>
              </select>
            </div>

            {/* Test Type */}
            <div>
              <label htmlFor="test_type" className="block text-sm font-medium text-gray-700">
                Test Type *
              </label>
              <select
                id="test_type"
                name="test_type"
                required
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                value={formData.test_type}
                onChange={handleInputChange}
                disabled={isLoading}
              >
                <option value={TestType.PCR}>PCR</option>
                <option value={TestType.CULTURE}>Culture</option>
                <option value={TestType.RAPID_MOLECULAR}>Rapid Molecular</option>
                <option value={TestType.ANTIGEN}>Antigen</option>
              </select>
            </div>

            {/* Specimen Collection Date */}
            <div>
              <label htmlFor="specimen_collection_date" className="block text-sm font-medium text-gray-700">
                Specimen Collection Date *
              </label>
              <input
                type="datetime-local"
                id="specimen_collection_date"
                name="specimen_collection_date"
                required
                className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  fieldErrors.specimen_collection_date ? 'border-red-500' : ''
                }`}
                value={formatDateTimeLocal(formData.specimen_collection_date)}
                onChange={handleInputChange}
                disabled={isLoading}
              />
              {fieldErrors.specimen_collection_date && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.specimen_collection_date}</p>
              )}
            </div>

            {/* Symptom Onset Date */}
            <div>
              <label htmlFor="symptom_onset_date" className="block text-sm font-medium text-gray-700">
                Symptom Onset Date
              </label>
              <input
                type="datetime-local"
                id="symptom_onset_date"
                name="symptom_onset_date"
                className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  fieldErrors.symptom_onset_date ? 'border-red-500' : ''
                }`}
                value={formatDateTimeLocal(formData.symptom_onset_date || '')}
                onChange={handleInputChange}
                disabled={isLoading}
              />
              {fieldErrors.symptom_onset_date && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.symptom_onset_date}</p>
              )}
            </div>

            {/* TEK Lookback Days */}
            <div>
              <label htmlFor="tek_lookback_days" className="block text-sm font-medium text-gray-700">
                TEK Lookback Days *
              </label>
              <input
                type="number"
                id="tek_lookback_days"
                name="tek_lookback_days"
                min="1"
                max="30"
                required
                className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  fieldErrors.tek_lookback_days ? 'border-red-500' : ''
                }`}
                value={formData.tek_lookback_days}
                onChange={handleInputChange}
                disabled={isLoading}
              />
              <p className="mt-1 text-xs text-gray-500">
                Auto-calculated based on pathogen type: {pathogenLookbackDays[formData.pathogen_type]} days
              </p>
              {fieldErrors.tek_lookback_days && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.tek_lookback_days}</p>
              )}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
              Additional Notes
            </label>
            <textarea
              id="notes"
              name="notes"
              rows={3}
              maxLength={1000}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              value={formData.notes || ''}
              onChange={handleInputChange}
              disabled={isLoading}
              placeholder="Enter any additional relevant information..."
            />
            <p className="mt-1 text-xs text-gray-500">
              {formData.notes?.length || 0}/1000 characters
            </p>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-3">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                disabled={isLoading}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isLoading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Saving...
                </span>
              ) : (
                initialData ? 'Update Case' : 'Create Case'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}