import { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowLeft, Printer } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function InvoiceView({ onLogout }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
    fetchInvoice();
  }, [id]);

  const fetchInvoice = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/invoices/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInvoice(response.data);
    } catch (error) {
      toast.error('Failed to load invoice');
      navigate('/invoices');
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
  };

  if (!invoice) {
    return (
      <Layout onLogout={onLogout}>
        <div className="flex items-center justify-center h-96">
          <p className="text-gray-500">Loading invoice...</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout onLogout={onLogout}>
      <div className="space-y-6" data-testid="invoice-view-page">
        <div className="flex justify-between items-center no-print">
          <Button variant="outline" onClick={() => navigate('/invoices')} data-testid="back-button">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Invoices
          </Button>
          <Button onClick={handlePrint} className="btn-primary text-white" data-testid="print-button">
            <Printer className="w-4 h-4 mr-2" />
            Print / Save PDF
          </Button>
        </div>

        <Card className="max-w-4xl mx-auto">
          <CardContent className="p-12">
            {/* Header */}
            <div className="flex justify-between items-start mb-12">
              <div>
                <h1 className="text-4xl font-bold text-gray-900 font-heading mb-2">INVOICE</h1>
                <p className="text-2xl font-semibold text-cyan-700" data-testid="invoice-number">{invoice.invoice_number}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">From</p>
                <p className="text-lg font-semibold text-gray-900">{user?.name || 'Your Company'}</p>
                <p className="text-sm text-gray-600">{user?.email}</p>
              </div>
            </div>

            {/* Client & Dates */}
            <div className="grid grid-cols-2 gap-8 mb-12">
              <div>
                <p className="text-sm text-gray-600 mb-2">Bill To</p>
                <p className="text-lg font-semibold text-gray-900" data-testid="client-name">{invoice.client_name}</p>
                {invoice.client_company && <p className="text-gray-600">{invoice.client_company}</p>}
                {invoice.client_email && <p className="text-gray-600">{invoice.client_email}</p>}
              </div>
              <div>
                <div className="mb-4">
                  <p className="text-sm text-gray-600">Invoice Date</p>
                  <p className="text-gray-900 font-medium" data-testid="invoice-date">{invoice.date}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Due Date</p>
                  <p className="text-gray-900 font-medium" data-testid="invoice-due-date">{invoice.due_date}</p>
                </div>
              </div>
            </div>

            {/* Items Table */}
            <div className="mb-8">
              <table className="w-full">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Description</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-700">Quantity</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-700">Rate</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-700">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {invoice.items.map((item, index) => (
                    <tr key={index} className="border-b" data-testid="invoice-item">
                      <td className="py-3 px-4">{item.description}</td>
                      <td className="text-right py-3 px-4">{item.quantity}</td>
                      <td className="text-right py-3 px-4">{formatCurrency(item.rate)}</td>
                      <td className="text-right py-3 px-4 font-medium">{formatCurrency(item.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Totals */}
            <div className="flex justify-end mb-8">
              <div className="w-64 space-y-3">
                <div className="flex justify-between text-gray-700">
                  <span>Subtotal:</span>
                  <span data-testid="invoice-subtotal">{formatCurrency(invoice.subtotal)}</span>
                </div>
                <div className="flex justify-between text-gray-700">
                  <span>Tax:</span>
                  <span data-testid="invoice-tax">{formatCurrency(invoice.tax)}</span>
                </div>
                <div className="flex justify-between text-gray-700">
                  <span>Discount:</span>
                  <span data-testid="invoice-discount">-{formatCurrency(invoice.discount)}</span>
                </div>
                <div className="flex justify-between text-xl font-bold text-gray-900 pt-3 border-t-2">
                  <span>Total:</span>
                  <span data-testid="invoice-total">{formatCurrency(invoice.total)}</span>
                </div>
              </div>
            </div>

            {/* Status */}
            <div className="mb-8">
              <span className={`status-badge status-${invoice.status} text-base`} data-testid="invoice-status">
                {invoice.status}
              </span>
            </div>

            {/* Notes */}
            {invoice.notes && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm font-semibold text-gray-700 mb-2">Notes:</p>
                <p className="text-gray-600" data-testid="invoice-notes">{invoice.notes}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
