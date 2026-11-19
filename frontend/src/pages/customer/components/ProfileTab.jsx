import React, { useState } from 'react';
import {
  User,
  Mail,
  Phone,
  Building,
  Calendar,
  Lock,
  Save,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
} from 'lucide-react';
import { updateCustomerProfile } from '../../../api/auth';

export const ProfileTab = ({ profile, onProfileUpdated }) => {
  const [formData, setFormData] = useState({
    full_name: profile?.full_name || '',
    phone: profile?.phone || '',
  });

  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (successMsg) setSuccessMsg('');
    if (errorMsg) setErrorMsg('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg('');
    setErrorMsg('');
    try {
      const updated = await updateCustomerProfile({
        full_name: formData.full_name.trim(),
        phone: formData.phone.trim() || undefined,
      });
      setSuccessMsg('Profile information updated successfully!');
      if (onProfileUpdated) onProfileUpdated(updated);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">My Customer Profile</h2>
          <p className="text-xs text-slate-500 mt-1">
            Personal identity details retrieved from the PostgreSQL database
          </p>
        </div>

        <div className="flex items-center space-x-2 px-3.5 py-1.5 bg-blue-50 border border-blue-200 rounded-xl text-blue-700 text-xs font-semibold">
          <ShieldCheck className="w-4 h-4 text-blue-600" />
          <span>Role: {profile?.role || 'CUSTOMER'}</span>
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center space-x-3 text-emerald-800 text-xs font-medium animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex items-center space-x-3 text-red-700 text-xs font-medium animate-fade-in">
          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Profile Form Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-sm space-y-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Permitted Editable Fields */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
              Permitted Contact Details
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Full Legal Name
                </label>
                <div className="relative rounded-xl shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <User className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    name="full_name"
                    required
                    value={formData.full_name}
                    onChange={handleChange}
                    className="block w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Phone Number
                </label>
                <div className="relative rounded-xl shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <Phone className="w-4 h-4" />
                  </div>
                  <input
                    type="tel"
                    name="phone"
                    placeholder="+1-555-0100"
                    value={formData.phone}
                    onChange={handleChange}
                    className="block w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Read-Only System Identity Fields */}
          <div className="pt-4 border-t border-slate-100">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
              Protected Identity Identifiers (Read-Only)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1.5 flex items-center justify-between">
                  <span>Customer Code</span>
                  <span className="flex items-center text-[10px] text-slate-400">
                    <Lock className="w-3 h-3 mr-1" /> System Controlled
                  </span>
                </label>
                <input
                  type="text"
                  disabled
                  value={profile?.customer_code || ''}
                  className="block w-full py-2.5 px-3.5 bg-slate-100/80 border border-slate-200 rounded-xl text-slate-600 text-xs font-mono font-bold cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1.5 flex items-center justify-between">
                  <span>Registered Email</span>
                  <span className="flex items-center text-[10px] text-slate-400">
                    <Lock className="w-3 h-3 mr-1" /> Immutable
                  </span>
                </label>
                <input
                  type="text"
                  disabled
                  value={profile?.email || ''}
                  className="block w-full py-2.5 px-3.5 bg-slate-100/80 border border-slate-200 rounded-xl text-slate-600 text-xs font-medium cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1.5 flex items-center justify-between">
                  <span>Assigned Branch</span>
                  <span className="flex items-center text-[10px] text-slate-400">
                    <Lock className="w-3 h-3 mr-1" /> Branch Controlled
                  </span>
                </label>
                <input
                  type="text"
                  disabled
                  value={profile?.branch_id || 'BR-MAIN-001 (Central)'}
                  className="block w-full py-2.5 px-3.5 bg-slate-100/80 border border-slate-200 rounded-xl text-slate-600 text-xs font-medium cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1.5 flex items-center justify-between">
                  <span>Member Since</span>
                  <span className="flex items-center text-[10px] text-slate-400">
                    <Lock className="w-3 h-3 mr-1" /> Immutable
                  </span>
                </label>
                <input
                  type="text"
                  disabled
                  value={profile?.created_at ? new Date(profile.created_at).toLocaleString() : 'N/A'}
                  className="block w-full py-2.5 px-3.5 bg-slate-100/80 border border-slate-200 rounded-xl text-slate-600 text-xs font-medium cursor-not-allowed"
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-4 border-t border-slate-100 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-md shadow-blue-500/20 transition disabled:opacity-60"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? 'Saving Changes...' : 'Save Profile Changes'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
