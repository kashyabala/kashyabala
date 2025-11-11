import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import Layout from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { DollarSign, FileText, Clock, AlertCircle, UserPlus } from 'lucide-react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#10b981', '#3b82f6', '#6b7280', '#ef4444'];
const ADMIN_EMAIL = 'kashyabalaa@gmail.com';

export default function Dashboard({ onLogout }) {
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [recentInvoices, setRecentInvoices] = useState([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [signupDialogOpen, setSignupDialogOpen] = useState(false);
  const [newUserForm, setNewUserForm] = useState({
    name: '',
    email: '',
    password: ''
  });

  useEffect(() => {
    fetchDashboardData();
    checkAdminStatus();
  }, []);

  const checkAdminStatus = () => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const adminStatus = user.email === ADMIN_EMAIL;
    console.log('Admin status:', adminStatus, 'for user:', user.email);
    setIsAdmin(adminStatus);
    if (adminStatus) {
      console.log('✅ Admin access granted!');
    }
  };

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [statsRes, chartRes, invoicesRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`, { headers }),
        axios.get(`${API}/dashboard/chart-data`, { headers }),
        axios.get(`${API}/invoices`, { headers })
      ]);

      setStats(statsRes.data);
      setChartData(chartRes.data);
      setRecentInvoices(invoicesRes.data.slice(0, 5));
    } catch (error) {
      toast.error('Failed to load dashboard data');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/auth/signup`, newUserForm);
      toast.success('User created successfully!');
      setSignupDialogOpen(false);
      setNewUserForm({ name: '', email: '', password: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    }
  };

  const statCards = stats ? [
    { title: 'Total Revenue', value: formatCurrency(stats.total_revenue), icon: DollarSign, color: 'bg-cyan-500', testId: 'stat-total-revenue' },
    { title: 'Paid Amount', value: formatCurrency(stats.paid_amount), icon: FileText, color: 'bg-green-500', testId: 'stat-paid-amount' },
    { title: 'Pending', value: formatCurrency(stats.pending_amount), icon: Clock, color: 'bg-blue-500', testId: 'stat-pending-amount' },
    { title: 'Overdue', value: formatCurrency(stats.overdue_amount), icon: AlertCircle, color: 'bg-red-500', testId: 'stat-overdue-amount' }
  ] : [];

  const pieData = chartData ? [
    { name: 'Paid', value: chartData.status_distribution.paid },
    { name: 'Sent', value: chartData.status_distribution.sent },
    { name: 'Draft', value: chartData.status_distribution.draft },
    { name: 'Overdue', value: chartData.status_distribution.overdue }
  ].filter(item => item.value > 0) : [];

  return (
    <Layout onLogout={onLogout}>
      <div className="space-y-8" data-testid="dashboard-page">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 font-heading">Dashboard</h1>
            <p className="text-gray-600 mt-2">Overview of your invoice management</p>
          </div>
          
          {/* Admin Only: Create User Button */}
          {isAdmin && (
            <Dialog open={signupDialogOpen} onOpenChange={setSignupDialogOpen}>
              <DialogTrigger asChild>
                <Button className="btn-primary text-white" data-testid="admin-create-user-button">
                  <UserPlus className="w-4 h-4 mr-2" />
                  Create New User
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="font-heading text-2xl">Create New User Account</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleCreateUser} className="space-y-4">
                  <div>
                    <Label htmlFor="new-name">Full Name *</Label>
                    <Input
                      id="new-name"
                      data-testid="admin-user-name-input"
                      type="text"
                      placeholder="John Doe"
                      value={newUserForm.name}
                      onChange={(e) => setNewUserForm({ ...newUserForm, name: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="new-email">Email *</Label>
                    <Input
                      id="new-email"
                      data-testid="admin-user-email-input"
                      type="email"
                      placeholder="user@example.com"
                      value={newUserForm.email}
                      onChange={(e) => setNewUserForm({ ...newUserForm, email: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="new-password">Password *</Label>
                    <Input
                      id="new-password"
                      data-testid="admin-user-password-input"
                      type="password"
                      placeholder="••••••••"
                      value={newUserForm.password}
                      onChange={(e) => setNewUserForm({ ...newUserForm, password: e.target.value })}
                      required
                    />
                  </div>
                  <div className="flex justify-end space-x-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setSignupDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" className="btn-primary text-white" data-testid="admin-create-user-submit">
                      Create User
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statCards.map((stat, index) => (
            <Card key={index} className="card-hover" data-testid={stat.testId}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  </div>
                  <div className={`${stat.color} p-3 rounded-xl`}>
                    <stat.icon className="w-6 h-6 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="font-heading">Revenue Trend</CardTitle>
            </CardHeader>
            <CardContent>
              {chartData && chartData.revenue_trend.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData.revenue_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="month" stroke="#6b7280" />
                    <YAxis stroke="#6b7280" />
                    <Tooltip />
                    <Line type="monotone" dataKey="revenue" stroke="#0891b2" strokeWidth={3} dot={{ fill: '#0891b2', r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-gray-500">
                  No revenue data available
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="font-heading">Invoice Status Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              {pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-gray-500">
                  No invoices created yet
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Recent Invoices */}
        <Card>
          <CardHeader>
            <CardTitle className="font-heading">Recent Invoices</CardTitle>
          </CardHeader>
          <CardContent>
            {recentInvoices.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Invoice #</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Client</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Date</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Amount</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentInvoices.map((invoice) => (
                      <tr key={invoice.id} className="border-b hover:bg-gray-50" data-testid="recent-invoice-row">
                        <td className="py-3 px-4 font-medium">{invoice.invoice_number}</td>
                        <td className="py-3 px-4">{invoice.client_name}</td>
                        <td className="py-3 px-4">{invoice.date}</td>
                        <td className="py-3 px-4 font-semibold">{formatCurrency(invoice.total)}</td>
                        <td className="py-3 px-4">
                          <span className={`status-badge status-${invoice.status}`}>
                            {invoice.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No invoices yet. Create your first invoice!</p>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
