'use client';

import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { KPIMetrics, RiskAlert, SystemHealth } from '../../../shared/types';

interface KPIWidgetProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
  };
  icon: React.ReactNode;
  color: 'primary' | 'success' | 'warning' | 'danger';
}

function KPIWidget({ title, value, subtitle, trend, icon, color }: KPIWidgetProps) {
  const colorClasses = {
    primary: 'bg-blue-50 text-blue-700',
    success: 'bg-green-50 text-green-700',
    warning: 'bg-yellow-50 text-yellow-700',
    danger: 'bg-red-50 text-red-700',
  };

  const iconColorClasses = {
    primary: 'text-blue-600',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    danger: 'text-red-600',
  };

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`inline-flex items-center justify-center p-3 rounded-md ${iconColorClasses[color]}`}>
              {icon}
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">{value}</div>
                {trend && (
                  <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                    trend.direction === 'up' ? 'text-green-600' :
                    trend.direction === 'down' ? 'text-red-600' : 'text-gray-500'
                  }`}>
                    {trend.direction === 'up' && (
                      <svg className="self-center flex-shrink-0 h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                    {trend.direction === 'down' && (
                      <svg className="self-center flex-shrink-0 h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                    {trend.value}%
                  </div>
                )}
              </dd>
              {subtitle && (
                <dd className="text-sm text-gray-500">{subtitle}</dd>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardOverview() {
  const [kpiMetrics, setKpiMetrics] = useState<KPIMetrics | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<RiskAlert[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const overviewData = await apiService.getDashboardOverview();

      setKpiMetrics(overviewData.kpi_metrics);
      setRecentAlerts(overviewData.recent_alerts);
      setSystemHealth(overviewData.system_health);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-red-800">{error}</div>
      </div>
    );
  }

  if (!kpiMetrics) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* KPI Widgets */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Key Performance Indicators</h2>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <KPIWidget
            title="Total Risk Alerts (24h)"
            value={kpiMetrics.total_alerts_24h}
            subtitle={`${kpiMetrics.high_risk_alerts_24h} high risk`}
            icon={
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            }
            color={kpiMetrics.high_risk_alerts_24h > 0 ? 'danger' : 'success'}
          />

          <KPIWidget
            title="TEK Upload Compliance"
            value={`${kpiMetrics.tek_upload_compliance_rate.toFixed(1)}%`}
            subtitle={`${kpiMetrics.total_active_cases} active cases`}
            trend={{
              value: 5.2,
              direction: kpiMetrics.tek_upload_compliance_rate > 80 ? 'up' : 'down'
            }}
            icon={
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            color={kpiMetrics.tek_upload_compliance_rate > 80 ? 'success' : 'warning'}
          />

          <KPIWidget
            title="New Cases (24h)"
            value={kpiMetrics.new_cases_24h}
            subtitle={`${kpiMetrics.new_cases_7d} this week`}
            icon={
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            }
            color={kpiMetrics.new_cases_24h > 5 ? 'warning' : 'primary'}
          />

          <KPIWidget
            title="Active Investigations"
            value={kpiMetrics.total_active_cases}
            subtitle="Across all wards"
            icon={
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            }
            color="primary"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Alerts */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Risk Alerts
            </h3>
            <div className="space-y-3">
              {recentAlerts.length === 0 ? (
                <p className="text-gray-500 text-sm">No recent alerts</p>
              ) : (
                recentAlerts.slice(0, 5).map((alert) => (
                  <div key={alert.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`flex-shrink-0 w-2 h-2 rounded-full ${
                        alert.alert_type === 'high' ? 'bg-red-500' :
                        alert.alert_type === 'moderate' ? 'bg-yellow-500' :
                        'bg-blue-500'
                      }`} />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {alert.location_identifier}
                        </p>
                        <p className="text-xs text-gray-500">
                          {alert.exposure_count} exposures • {alert.confidence_score.toFixed(1)}% confidence
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">
                        {new Date(alert.created_at).toLocaleTimeString()}
                      </p>
                      {!alert.acknowledged_at && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                          New
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* System Health */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              System Health
            </h3>
            <div className="space-y-3">
              {systemHealth.length === 0 ? (
                <p className="text-gray-500 text-sm">No system health data available</p>
              ) : (
                systemHealth.map((health) => (
                  <div key={health.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`flex-shrink-0 w-2 h-2 rounded-full ${
                        health.status === 'healthy' ? 'bg-green-500' :
                        health.status === 'degraded' ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`} />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {health.service_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {health.response_time_ms ? `${health.response_time_ms}ms` : 'N/A'} • {health.uptime_percentage.toFixed(1)}% uptime
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        health.status === 'healthy' ? 'bg-green-100 text-green-800' :
                        health.status === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {health.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Pathogen Distribution */}
      {Object.keys(kpiMetrics.pathogen_distribution).length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Pathogen Distribution
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(kpiMetrics.pathogen_distribution).map(([pathogen, count]) => (
                <div key={pathogen} className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{count}</div>
                  <div className="text-xs text-gray-500 mt-1">{pathogen.replace('_', ' ')}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}