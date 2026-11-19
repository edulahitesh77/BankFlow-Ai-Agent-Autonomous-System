import React, { useState } from 'react';
import {
  FileText,
  CreditCard,
  MapPin,
  UserPlus,
  Send,
  AlertCircle,
  CheckCircle2,
  ShieldAlert,
  ArrowRight,
  Info,
} from 'lucide-react';
import { submitServiceRequest } from '../../../api/auth';

export const NewRequestTab = ({ accounts = [], onNavigateTab, onSelectRequest, onRefreshRequests }) => {
  const [selectedService, setSelectedService] = useState('CHEQUE_BOOK');
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [submittedRequestId, setSubmittedRequestId] = useState(null);

  // Form states
  const [chequeForm, setChequeForm] = useState({
    account_id: accounts[0]?.id || '',
    cheque_leaves: 25,
    delivery_preference: 'Standard Postal',
    remarks: '',
  });

  const [cardForm, setCardForm] = useState({
    account_id: accounts[0]?.id || '',
    replacement_reason: 'Damaged Card',
    remarks: '',
  });

  const [addressForm, setAddressForm] = useState({
    account_id: accounts[0]?.id || '',
    new_synthetic_address: '',
    city: '',
    state: '',
    postal_code: '',
    reason_for_update: 'Relocated residence',
  });

  const [appForm, setAppForm] = useState({
    applicant_name: '',
    email: '',
    phone: '',
    requested_account_type: 'SAVINGS',
    branch_preference: 'Main Downtown Branch',
    remarks: '',
  });

  const services = [
    {
      id: 'CHEQUE_BOOK',
      title: 'Cheque Book Request',
      icon: FileText,
      description: 'Order personalized cheque leaf books with postal or branch delivery options.',
      badge: 'Operational',
    },
    {
      id: 'DEBIT_CARD_REPLACEMENT',
      title: 'Debit Card Replacement',
      icon: CreditCard,
      description: 'Request a simulated replacement card due to damage, loss, or renewal.',
      badge: 'Operational',
    },
    {
      id: 'ADDRESS_UPDATE',
      title: 'Address Update',
      icon: MapPin,
      description: 'Update your official billing and correspondence address for bank records.',
      badge: 'Simulated',
    },
    {
      id: 'ACCOUNT_APPLICATION',
      title: 'Account Application Pre-Screening',
      icon: UserPlus,
      description: 'Submit preliminary information for automated account eligibility evaluation.',
      badge: 'Pre-Screening',
    },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSubmittedRequestId(null);
    setSubmitting(true);

    try {
      let requestPayload = {};
      let targetAccountId = null;

      if (selectedService === 'CHEQUE_BOOK') {
        if (!chequeForm.account_id) throw new Error('Please select an account.');
        targetAccountId = parseInt(chequeForm.account_id, 10);
        requestPayload = {
          service_type: 'CHEQUE_BOOK',
          account_id: targetAccountId,
          priority: 'MEDIUM',
          payload: {
            account_id: targetAccountId,
            cheque_leaves: parseInt(chequeForm.cheque_leaves, 10),
            delivery_preference: chequeForm.delivery_preference,
            remarks: chequeForm.remarks || undefined,
          },
        };
      } else if (selectedService === 'DEBIT_CARD_REPLACEMENT') {
        if (!cardForm.account_id) throw new Error('Please select an account.');
        targetAccountId = parseInt(cardForm.account_id, 10);
        requestPayload = {
          service_type: 'DEBIT_CARD_REPLACEMENT',
          account_id: targetAccountId,
          priority: 'HIGH',
          payload: {
            account_id: targetAccountId,
            replacement_reason: cardForm.replacement_reason,
            remarks: cardForm.remarks || undefined,
          },
        };
      } else if (selectedService === 'ADDRESS_UPDATE') {
        if (!addressForm.account_id) throw new Error('Please select an account.');
        targetAccountId = parseInt(addressForm.account_id, 10);
        requestPayload = {
          service_type: 'ADDRESS_UPDATE',
          account_id: targetAccountId,
          priority: 'MEDIUM',
          payload: {
            account_id: targetAccountId,
            new_synthetic_address: addressForm.new_synthetic_address,
            city: addressForm.city,
            state: addressForm.state,
            postal_code: addressForm.postal_code,
            reason_for_update: addressForm.reason_for_update,
          },
        };
      } else if (selectedService === 'ACCOUNT_APPLICATION') {
        requestPayload = {
          service_type: 'ACCOUNT_APPLICATION',
          account_id: null,
          priority: 'MEDIUM',
          payload: {
            applicant_name: appForm.applicant_name,
            email: appForm.email,
            phone: appForm.phone,
            requested_account_type: appForm.requested_account_type,
            branch_preference: appForm.branch_preference,
            remarks: appForm.remarks || undefined,
          },
        };
      }

      const res = await submitServiceRequest(requestPayload);
      setSubmittedRequestId(res.request_id);
      if (onRefreshRequests) onRefreshRequests();
    } catch (err) {
      setErrorMessage(err.message || 'Submission failed. Please check form parameters.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
      {/* Title */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900">New Banking Service Request</h2>
        <p className="text-xs text-slate-500 mt-1">
          Select a banking service below to initiate an automated multi-agent workflow
        </p>
      </div>

      {/* Service Selection Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {services.map((svc) => {
          const Icon = svc.icon;
          const isSelected = selectedService === svc.id;
          return (
            <div
              key={svc.id}
              onClick={() => {
                setSelectedService(svc.id);
                setErrorMessage('');
                setSubmittedRequestId(null);
              }}
              className={`p-5 rounded-3xl border transition cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'bg-blue-50/80 border-blue-600 shadow-md ring-2 ring-blue-500/20'
                  : 'bg-white border-slate-200 hover:border-slate-300 shadow-sm'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div
                    className={`w-10 h-10 rounded-2xl flex items-center justify-center ${
                      isSelected ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      isSelected ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {svc.badge}
                  </span>
                </div>
                <h3 className="font-bold text-sm text-slate-900 leading-snug">{svc.title}</h3>
                <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{svc.description}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Success Notification Banner */}
      {submittedRequestId && (
        <div className="p-6 rounded-3xl bg-emerald-50 border border-emerald-200 shadow-sm space-y-3 animate-fade-in">
          <div className="flex items-center space-x-3 text-emerald-800">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
            <div>
              <h4 className="font-bold text-sm">Service Request Created Successfully!</h4>
              <p className="text-xs text-emerald-700">
                Your request has been registered in the database with status <strong>NEW</strong>.
              </p>
            </div>
          </div>
          <div className="p-3 bg-white/80 rounded-2xl border border-emerald-200/80 flex items-center justify-between">
            <span className="text-xs text-slate-600">Assigned Request ID:</span>
            <span className="font-mono text-sm font-bold text-slate-900">{submittedRequestId}</span>
          </div>
          <div className="pt-2 flex space-x-3">
            <button
              onClick={() => {
                onSelectRequest(submittedRequestId);
                onNavigateTab('track_request');
              }}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold transition shadow-sm"
            >
              <span>Track This Request Now</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setSubmittedRequestId(null)}
              className="px-4 py-2 bg-white text-slate-700 hover:bg-slate-50 rounded-xl text-xs font-semibold border border-slate-200 transition"
            >
              Submit Another
            </button>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex items-start space-x-3 text-red-700 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-500" />
          <div className="flex-1 font-medium">{errorMessage}</div>
        </div>
      )}

      {/* Service Specific Form Container */}
      {!submittedRequestId && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-sm space-y-6">
          {/* Header of active form */}
          <div className="border-b border-slate-100 pb-4">
            <h3 className="text-lg font-bold text-slate-900">
              {services.find((s) => s.id === selectedService)?.title}
            </h3>
            <p className="text-xs text-slate-500">
              Complete the required parameters below. Form inputs will be saved into PostgreSQL.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Account Selector (for Services 1, 2, and 3) */}
            {selectedService !== 'ACCOUNT_APPLICATION' && (
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Select Synthetic Account *
                </label>
                {accounts.length > 0 ? (
                  <select
                    value={
                      selectedService === 'CHEQUE_BOOK'
                        ? chequeForm.account_id
                        : selectedService === 'DEBIT_CARD_REPLACEMENT'
                        ? cardForm.account_id
                        : addressForm.account_id
                    }
                    onChange={(e) => {
                      const val = e.target.value;
                      if (selectedService === 'CHEQUE_BOOK') setChequeForm((p) => ({ ...p, account_id: val }));
                      else if (selectedService === 'DEBIT_CARD_REPLACEMENT') setCardForm((p) => ({ ...p, account_id: val }));
                      else setAddressForm((p) => ({ ...p, account_id: val }));
                    }}
                    required
                    className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">-- Choose Account --</option>
                    {accounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>
                        {acc.synthetic_account_number} ({acc.account_type}) - Branch: {acc.branch_id || 'Main'}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-center justify-between">
                    <span>No synthetic accounts found. Please generate a demo account first.</span>
                    <button
                      type="button"
                      onClick={() => onNavigateTab('accounts')}
                      className="px-3 py-1 bg-amber-600 text-white rounded-lg font-semibold"
                    >
                      Go to My Accounts
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* SERVICE 1: CHEQUE BOOK FIELDS */}
            {selectedService === 'CHEQUE_BOOK' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Number of Cheque Leaves *
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {[25, 50, 100].map((leaves) => (
                      <button
                        key={leaves}
                        type="button"
                        onClick={() => setChequeForm((p) => ({ ...p, cheque_leaves: leaves }))}
                        className={`py-3 rounded-xl border text-xs font-bold transition ${
                          chequeForm.cheque_leaves === leaves
                            ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                            : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                        }`}
                      >
                        {leaves} Leaves
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Delivery Preference *
                  </label>
                  <select
                    value={chequeForm.delivery_preference}
                    onChange={(e) => setChequeForm((p) => ({ ...p, delivery_preference: e.target.value }))}
                    className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Standard Postal">Standard Postal Delivery (Simulated)</option>
                    <option value="Branch Pickup">Branch Pickup (Main Counter)</option>
                    <option value="Express Delivery">Express Courier Delivery</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Optional Remarks
                  </label>
                  <textarea
                    rows={2}
                    placeholder="e.g. Include personalized name imprint..."
                    value={chequeForm.remarks}
                    onChange={(e) => setChequeForm((p) => ({ ...p, remarks: e.target.value }))}
                    className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}

            {/* SERVICE 2: DEBIT CARD REPLACEMENT FIELDS */}
            {selectedService === 'DEBIT_CARD_REPLACEMENT' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Replacement Reason *
                  </label>
                  <select
                    value={cardForm.replacement_reason}
                    onChange={(e) => setCardForm((p) => ({ ...p, replacement_reason: e.target.value }))}
                    className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Damaged Card">Damaged Card (Physical or EMV Chip wear)</option>
                    <option value="Lost Card (simulation only)">Lost Card (Simulation only)</option>
                    <option value="Other">Other Reason</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Optional Remarks
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Details about card damage or replacement requirements..."
                    value={cardForm.remarks}
                    onChange={(e) => setCardForm((p) => ({ ...p, remarks: e.target.value }))}
                    className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="p-3 bg-slate-100 rounded-xl flex items-start space-x-2 text-xs text-slate-600">
                  <ShieldAlert className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
                  <span>
                    <strong>Security Notice:</strong> BankFlow AI never collects actual card numbers, PINs, or CVV codes. Replacement is handled using synthetic identifiers.
                  </span>
                </div>
              </div>
            )}

            {/* SERVICE 3: ADDRESS UPDATE FIELDS */}
            {selectedService === 'ADDRESS_UPDATE' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    New Synthetic Street Address *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 100 Innovation Boulevard, Suite 400"
                    value={addressForm.new_synthetic_address}
                    onChange={(e) => setAddressForm((p) => ({ ...p, new_synthetic_address: e.target.value }))}
                    className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      City *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Metro City"
                      value={addressForm.city}
                      onChange={(e) => setAddressForm((p) => ({ ...p, city: e.target.value }))}
                      className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      State / Province *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. California"
                      value={addressForm.state}
                      onChange={(e) => setAddressForm((p) => ({ ...p, state: e.target.value }))}
                      className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      Postal Code *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. 90210"
                      value={addressForm.postal_code}
                      onChange={(e) => setAddressForm((p) => ({ ...p, postal_code: e.target.value }))}
                      className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Reason for Address Update *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Relocated to new home address"
                    value={addressForm.reason_for_update}
                    onChange={(e) => setAddressForm((p) => ({ ...p, reason_for_update: e.target.value }))}
                    className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-xl flex items-start space-x-2 text-xs text-blue-900">
                  <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                  <span>
                    Simulated address update workflow. Real personal identity documents are not collected in this simulation.
                  </span>
                </div>
              </div>
            )}

            {/* SERVICE 4: ACCOUNT APPLICATION PRE-SCREENING FIELDS */}
            {selectedService === 'ACCOUNT_APPLICATION' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      Applicant Full Name *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="Legal full name"
                      value={appForm.applicant_name}
                      onChange={(e) => setAppForm((p) => ({ ...p, applicant_name: e.target.value }))}
                      className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      Contact Email *
                    </label>
                    <input
                      type="email"
                      required
                      placeholder="applicant@example.com"
                      value={appForm.email}
                      onChange={(e) => setAppForm((p) => ({ ...p, email: e.target.value }))}
                      className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      Phone Number *
                    </label>
                    <input
                      type="tel"
                      required
                      placeholder="+1-555-0100"
                      value={appForm.phone}
                      onChange={(e) => setAppForm((p) => ({ ...p, phone: e.target.value }))}
                      className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      Account Type *
                    </label>
                    <select
                      value={appForm.requested_account_type}
                      onChange={(e) => setAppForm((p) => ({ ...p, requested_account_type: e.target.value }))}
                      className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="SAVINGS">Savings Account</option>
                      <option value="CHECKING">Checking Account</option>
                      <option value="FIXED_DEPOSIT">Fixed Deposit</option>
                      <option value="MONEY_MARKET">Money Market</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      Branch Preference *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="Branch location"
                      value={appForm.branch_preference}
                      onChange={(e) => setAppForm((p) => ({ ...p, branch_preference: e.target.value }))}
                      className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Optional Remarks
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Any specific banking requirements or questions..."
                    value={appForm.remarks}
                    onChange={(e) => setAppForm((p) => ({ ...p, remarks: e.target.value }))}
                    className="block w-full py-2.5 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start space-x-2 text-xs text-amber-800">
                  <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  <span>
                    <strong>Educational Pre-Screening Only:</strong> Submitting this form simulates application completeness verification by autonomous agents. It will never open an actual bank account.
                  </span>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-blue-500/25 transition disabled:opacity-60"
              >
                <Send className="w-4 h-4" />
                <span>{submitting ? 'Submitting to Database...' : 'Submit Service Request'}</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
