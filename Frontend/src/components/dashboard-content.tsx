"use client";

import { DashboardHeader } from "@/components/dashboard/header";
import { ApiLoadingOverlay } from "@/components/dashboard/loading-overlay";
import { ResultPanel } from "@/components/dashboard/result-panel";
import {
  CloudProcessingSection,
  CloudUploadSection,
  LocalProcessingSection,
  TenantCloudSection,
} from "@/components/dashboard/sections";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDashboardState } from "@/components/dashboard/use-dashboard-state";

export const DashboardContent = () => {
  const dashboard = useDashboardState();

  return (
    <>
      {dashboard.isAnyApiLoading ? (
        <ApiLoadingOverlay actionLabel={dashboard.activeActionLabel} />
      ) : null}
      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-6 bg-gradient-to-b from-blue-50 via-white to-slate-100 px-4 py-8 text-slate-900 md:px-8">
        <DashboardHeader status={dashboard.healthStatus} hasError={dashboard.healthError} />

        <div className="grid gap-6 lg:grid-cols-[1.3fr_0.9fr]">
          <Tabs defaultValue="cloud" className="space-y-4">
            <TabsList className="w-full justify-start gap-2 rounded-xl bg-white p-1 shadow-sm">
              <TabsTrigger
                value="cloud"
                className="cursor-pointer px-4 text-slate-600 data-active:bg-blue-600 data-active:text-white"
              >
                Cloud
              </TabsTrigger>
              <TabsTrigger
                value="tenant"
                className="cursor-pointer px-4 text-slate-600 data-active:bg-indigo-600 data-active:text-white"
              >
                Tenant Cloud
              </TabsTrigger>
              <TabsTrigger
                value="local"
                className="cursor-pointer px-4 text-slate-600 data-active:bg-slate-800 data-active:text-white"
              >
                Local
              </TabsTrigger>
            </TabsList>

            <TabsContent value="cloud" className="space-y-6">
              <CloudUploadSection onUpload={dashboard.runCloudUpload} />
              <CloudProcessingSection
                isCloudBatchPending={dashboard.cloudBatchPending}
                onCloudBatch={dashboard.runCloudBatch}
                onCloudOne={dashboard.runCloudOne}
              />
            </TabsContent>

            <TabsContent value="tenant">
              <TenantCloudSection
                currentConfigId={dashboard.tenantConfigId}
                isTenantCloudBatchPending={dashboard.tenantCloudBatchPending}
                onConfigRegister={dashboard.handleRegisterConfig}
                onConfigSelect={dashboard.setTenantConfigId}
                onTenantCloudUpload={dashboard.handleTenantUpload}
                onTenantCloudBatch={dashboard.runTenantCloudBatch}
                onTenantCloudOne={dashboard.runTenantCloudOne}
              />
            </TabsContent>

            <TabsContent value="local">
              <LocalProcessingSection
                isLocalBatchPending={dashboard.localBatchPending}
                onLocalBatch={dashboard.runLocalBatch}
                onLocalOne={dashboard.runLocalOne}
              />
            </TabsContent>
          </Tabs>

          <ResultPanel messages={dashboard.messages} />
        </div>
      </main>
    </>
  );
};
