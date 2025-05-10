import { cookies } from 'next/headers';

import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import { auth } from '../(auth)/auth';
import Script from 'next/script';
import TimeTable from '@/components/timetable';     

export const experimental_ppr = true;

export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [session, cookieStore] = await Promise.all([auth(), cookies()]);
  const isCollapsed = cookieStore.get('sidebar:state')?.value !== 'true';

  return (
    <>
      <Script
        src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"
        strategy="beforeInteractive"
      />
      <SidebarProvider defaultOpen={!isCollapsed}>
        <div className="relative flex h-full w-full overflow-hidden">
          {session?.user && <AppSidebar user={session.user} />}
          <div className="group flex flex-1 w-full overflow-hidden pl-0 peer-[[data-state=open]]:lg:pl-[16rem] peer-[[data-state=open]]:xl:pl-[18rem]">
            <main className="flex-1 overflow-y-auto">
              {children}
            </main>
            <aside className="w-[380px] flex-col border-l border-border bg-sidebar p-4 overflow-y-auto hidden md:flex">
              <TimeTable rows={15} cols={7} />
            </aside>
          </div>
        </div>
      </SidebarProvider>
    </>
  );
}
