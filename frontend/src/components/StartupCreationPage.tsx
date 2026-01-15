import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, FileText, MapPin, Users, Briefcase, ArrowLeft, Hash } from 'lucide-react';
import { Navigation } from './Navigation';
import * as api from '../api';
import { useAuth } from '../AuthContext';

export function StartupCreationPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [founderId, setFounderId] = useState('');
  const [name, setName] = useState('');
  const [matriculeFiscal, setMatriculeFiscal] = useState('');
  const [rneNumber, setRneNumber] = useState('');
  const [legalForm, setLegalForm] = useState('SARL');
  const [field, setField] = useState('tech');
  const [sector, setSector] = useState('private');
  const [size, setSize] = useState('small');
  const [location, setLocation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleNavigate = (page: string) => {
    if (page === 'reminders') {
      navigate('/reminders');
    } else if (page === 'admin-dashboard') {
      navigate('/dashboard/admin');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    
    if (!founderId || isNaN(parseInt(founderId))) {
      setError('Please enter a valid Founder ID');
      return;
    }
    
    try {
      setIsSubmitting(true);
      await api.createStartupByAdmin({
        founder_id: parseInt(founderId),
        name,
        matricule_fiscal: matriculeFiscal,
        rne_number: rneNumber,
        legal_form: legalForm,
        field,
        sector,
        size,
        location
      });
      setSuccess(true);
      setTimeout(() => {
        navigate('/dashboard/admin');
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create startup');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {user && <Navigation user={user} onNavigate={handleNavigate} onLogout={logout} currentPage="admin-dashboard" />}
    <div className="container mx-auto px-4 py-8">
      <button
        onClick={() => navigate('/dashboard/admin')}
        className="flex items-center text-gray-600 hover:text-gray-900 mb-8 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Dashboard
      </button>

      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <Building2 className="w-8 h-8 text-green-600" />
            </div>
          </div>

          <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">
            Create Startup
          </h2>
          <p className="text-center text-gray-600 mb-8">
            Register a new startup in the system
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-600">
              Startup created successfully! Redirecting...
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="founderId" className="block text-sm font-medium text-gray-700 mb-2">
                Founder ID *
              </label>
              <div className="relative">
                <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="founderId"
                  type="number"
                  value={founderId}
                  onChange={(e) => setFounderId(e.target.value)}
                  placeholder="12345"
                  className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                  required
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">Enter the User ID of the startup founder/owner</p>
            </div>

            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Startup Name *
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="TechStart Inc."
                  className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="matriculeFiscal" className="block text-sm font-medium text-gray-700 mb-2">
                  Matricule Fiscal *
                </label>
                <div className="relative">
                  <FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    id="matriculeFiscal"
                    type="text"
                    value={matriculeFiscal}
                    onChange={(e) => setMatriculeFiscal(e.target.value)}
                    placeholder="1234567X"
                    className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                    required
                  />
                </div>
              </div>

              <div>
                <label htmlFor="rneNumber" className="block text-sm font-medium text-gray-700 mb-2">
                  RNE Number *
                </label>
                <div className="relative">
                  <FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    id="rneNumber"
                    type="text"
                    value={rneNumber}
                    onChange={(e) => setRneNumber(e.target.value)}
                    placeholder="B123456789"
                    className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="legalForm" className="block text-sm font-medium text-gray-700 mb-2">
                  Legal Form *
                </label>
                <div className="relative">
                  <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <select
                    id="legalForm"
                    value={legalForm}
                    onChange={(e) => setLegalForm(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all appearance-none bg-white"
                    required
                  >
                    <option value="SARL">SARL</option>
                    <option value="SA">SA</option>
                    <option value="SAS">SAS</option>
                    <option value="SUARL">SUARL</option>
                    <option value="SNC">SNC</option>
                  </select>
                </div>
              </div>

              <div>
                <label htmlFor="field" className="block text-sm font-medium text-gray-700 mb-2">
                  Field *
                </label>
                <div className="relative">
                  <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <select
                    id="field"
                    value={field}
                    onChange={(e) => setField(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all appearance-none bg-white"
                    required
                  >
                    <option value="tech">Technology</option>
                    <option value="healthcare">Healthcare</option>
                    <option value="finance">Finance</option>
                    <option value="manufacturing">Manufacturing</option>
                    <option value="retail">Retail</option>
                    <option value="services">Services</option>
                    <option value="education">Education</option>
                    <option value="agriculture">Agriculture</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="sector" className="block text-sm font-medium text-gray-700 mb-2">
                  Sector *
                </label>
                <div className="relative">
                  <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <select
                    id="sector"
                    value={sector}
                    onChange={(e) => setSector(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all appearance-none bg-white"
                    required
                  >
                    <option value="private">Private</option>
                    <option value="public">Public</option>
                    <option value="ngo">NGO</option>
                  </select>
                </div>
              </div>

              <div>
                <label htmlFor="size" className="block text-sm font-medium text-gray-700 mb-2">
                  Size *
                </label>
                <div className="relative">
                  <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <select
                    id="size"
                    value={size}
                    onChange={(e) => setSize(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all appearance-none bg-white"
                    required
                  >
                    <option value="small">Small (1-50)</option>
                    <option value="medium">Medium (51-250)</option>
                    <option value="large">Large (250+)</option>
                  </select>
                </div>
              </div>
            </div>

            <div>
              <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
                Location *
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="location"
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Tunis, Tunisia"
                  className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                  required
                />
              </div>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800">
                <strong>Note:</strong> Make sure the Founder ID corresponds to an existing user with the "Owner" role in the system.
              </p>
            </div>

            <div className="flex space-x-4">
              <button
                type="button"
                onClick={() => navigate('/dashboard/admin')}
                className="flex-1 bg-gray-200 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating...' : 'Create Startup'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
    </>
  );
}
