import React, { useMemo, useState } from "react";

type Theme = "legacy" | "corsair";

interface TableRow {
  id: string;
  status: string;
  updated: string;
  owner: string;
  favorite: boolean;
}

const mockRows: TableRow[] = [
  { id: "VX-204", status: "Aktiv", updated: "07.11.2025 10:24", owner: "T. Hartung", favorite: true },
  { id: "VX-205", status: "Geplant", updated: "07.11.2025 09:18", owner: "B. Schmidt", favorite: false },
  { id: "VX-198", status: "Archiviert", updated: "06.11.2025 15:02", owner: "A. Nguyen", favorite: true },
  { id: "VX-190", status: "Aktiv", updated: "06.11.2025 12:44", owner: "S. Hoffmann", favorite: false },
  { id: "VX-177", status: "Wartung", updated: "05.11.2025 21:11", owner: "M. Weber", favorite: false },
];

const App: React.FC = () => {
  const [theme, setTheme] = useState<Theme>("corsair");

  const prefersReducedMotion = useMemo(() => {
    if (typeof window === "undefined") {
      return true;
    }
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  const toggleTheme = () => setTheme((prev) => (prev === "legacy" ? "corsair" : "legacy"));

  return (
    <div
      className={
        theme === "corsair"
          ? "min-h-screen bg-black text-white font-sf antialiased transition-colors duration-200"
          : "min-h-screen bg-slate-100 text-slate-900 font-sf antialiased"
      }
    >
      <TopBar theme={theme} />
      <div className="flex min-h-[calc(100vh-72px)]">
        <Sidebar theme={theme} />
        <main className="flex-1 px-6 py-8 lg:px-10">
          {theme === "corsair" ? (
            <MainTable prefersReducedMotion={prefersReducedMotion} />
          ) : (
            <LegacyPlaceholder />
          )}
        </main>
      </div>
      <FooterInfo theme={theme} />
      <DesignSwitchButton theme={theme} onToggle={toggleTheme} />
    </div>
  );
};

const TopBar: React.FC<{ theme: Theme }> = ({ theme }) => (
  <header
    className={
      theme === "corsair"
        ? "flex items-center gap-4 border-b border-white/20 px-6 py-4 lg:px-10"
        : "flex items-center gap-4 bg-white px-6 py-4 shadow-sm lg:px-10"
    }
  >
    <Logo theme={theme} />
    <div className="flex flex-col">
      <span className={theme === "corsair" ? "text-sm uppercase tracking-[0.2em] text-white/60" : "text-xs uppercase tracking-[0.3em] text-slate-500"}>
        Corsair
      </span>
      <h1 className={theme === "corsair" ? "text-xl font-semibold text-white" : "text-2xl font-semibold text-slate-900"}>
        Operations Dashboard
      </h1>
    </div>
  </header>
);

const Sidebar: React.FC<{ theme: Theme }> = ({ theme }) => (
  <aside
    className={
      theme === "corsair"
        ? "hidden w-64 border-r border-white/15 bg-black/60 backdrop-blur lg:flex lg:flex-col"
        : "hidden w-64 border-r border-slate-200 bg-white lg:flex lg:flex-col"
    }
  >
    <nav className="flex-1 space-y-6 px-6 py-8">
      <SectionTitle theme={theme} label="Übersicht" />
      <SidebarItem theme={theme} label="Aktuelle Tabelle" active />
      <SidebarItem theme={theme} label="Berichte" />
      <SidebarItem theme={theme} label="Historie" />
      <SectionTitle theme={theme} label="Teams" />
      <SidebarItem theme={theme} label="Performance Crew" />
      <SidebarItem theme={theme} label="Audio Ops" />
      <SidebarItem theme={theme} label="Editor Lab" />
    </nav>
  </aside>
);

const SectionTitle: React.FC<{ theme: Theme; label: string }> = ({ theme, label }) => (
  <p className={theme === "corsair" ? "text-xs font-medium uppercase tracking-[0.2em] text-white/40" : "text-xs font-semibold uppercase tracking-[0.2em] text-slate-500"}>
    {label}
  </p>
);

const SidebarItem: React.FC<{ theme: Theme; label: string; active?: boolean }> = ({ theme, label, active }) => {
  const base = "block w-full rounded-xl px-4 py-3 text-sm transition-colors duration-150";

  if (theme === "corsair") {
    return (
      <button
        type="button"
        className={
          base +
          " text-left " +
          (active ? "bg-white text-black" : "text-white/80 hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-white/40")
        }
      >
        {label}
      </button>
    );
  }

  return (
    <button
      type="button"
      className={
        base +
        " text-left " +
        (active ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-slate-400/60")
      }
    >
      {label}
    </button>
  );
};

const MainTable: React.FC<{ prefersReducedMotion: boolean }> = ({ prefersReducedMotion }) => (
  <section className="space-y-6">
    <header className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div>
        <h2 className="text-2xl font-semibold text-white">Corsair 3.0 · Aktuelle Tabelle</h2>
        <p className="text-sm text-white/60">Schlanke, lesbare Übersicht der wichtigsten Produktionsläufe.</p>
      </div>
      <div className="flex items-center gap-3">
        <GoldIcon />
        <span className="text-xs uppercase tracking-[0.3em] text-white/50">Version 3.0</span>
      </div>
    </header>

    <div className="overflow-hidden rounded-2xl border border-white/15 bg-black/80">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-white/5 text-left text-xs uppercase tracking-[0.2em] text-white/70">
            <th className="px-6 py-4">ID</th>
            <th className="px-6 py-4">Status</th>
            <th className="px-6 py-4">Zuletzt aktualisiert</th>
            <th className="px-6 py-4">Owner</th>
            <th className="px-6 py-4">Favorit</th>
          </tr>
        </thead>
        <tbody>
          {mockRows.map((row, index) => (
            <tr
              key={row.id}
              className={
                "transition-all " +
                (prefersReducedMotion ? "" : "duration-150 ease-out") +
                (index % 2 === 0 ? " bg-white/0" : " bg-white/[0.04]") +
                " hover:bg-white/[0.08] focus-within:bg-white/[0.12] hover:outline hover:outline-1 hover:outline-white/40"
              }
            >
              <td className="px-6 py-5 text-sm font-medium text-white">{row.id}</td>
              <td className="px-6 py-5 text-sm text-white/80">{row.status}</td>
              <td className="px-6 py-5 text-sm text-white/70">{row.updated}</td>
              <td className="px-6 py-5 text-sm text-white/80">{row.owner}</td>
              <td className="px-6 py-5">
                <span className="inline-flex items-center justify-center rounded-full border border-white/20 px-3 py-1 text-xs text-white/70">
                  {row.favorite ? <GoldIcon /> : "—"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </section>
);

const GoldIcon: React.FC = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 20 20"
    aria-hidden
    className="shrink-0"
    style={{ fill: "var(--gold)", opacity: 0.9 }}
  >
    <path d="M9.999 1.5l2.414 5.07 5.588.812-4.027 3.926.951 5.547-4.926-2.593-4.926 2.593.951-5.547-4.027-3.926 5.588-.812L9.999 1.5z" />
  </svg>
);

const LegacyPlaceholder: React.FC = () => (
  <div className="rounded-3xl border border-slate-200 bg-white px-8 py-12 shadow-lg">
    <h2 className="text-3xl font-semibold text-slate-900">Legacy UI</h2>
    <p className="mt-3 text-slate-600">
      Dies ist eine Platzhalter-Ansicht für das bestehende System. Inhalte, Farben und Interaktionen entsprechen dem bisherigen Stand.
    </p>
    <div className="mt-8 grid gap-6 md:grid-cols-2">
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
        <h3 className="text-lg font-semibold text-slate-900">Konfiguration</h3>
        <p className="mt-2 text-sm text-slate-600">Aktuelle Einstellungen, Filter und Debug-Optionen werden hier angezeigt.</p>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
        <h3 className="text-lg font-semibold text-slate-900">Aktivitäten</h3>
        <p className="mt-2 text-sm text-slate-600">Verlauf und Statistiken des bisherigen Systems bleiben unverändert.</p>
      </div>
    </div>
  </div>
);

const FooterInfo: React.FC<{ theme: Theme }> = ({ theme }) => (
  <footer
    className={
      theme === "corsair"
        ? "pointer-events-none fixed bottom-6 left-6 text-xs text-white/60"
        : "pointer-events-none fixed bottom-6 left-6 text-xs text-slate-500"
    }
  >
    Standard-Einstellungen aktiv: Tabelle=Aktuell · Sprache=System · Debug=Aus
  </footer>
);

const DesignSwitchButton: React.FC<{ theme: Theme; onToggle: () => void }> = ({ theme, onToggle }) => (
  <button
    type="button"
    onClick={onToggle}
    className={
      theme === "corsair"
        ? "fixed bottom-6 right-6 rounded-full bg-white px-6 py-3 text-sm font-semibold text-black transition-transform hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-white/60"
        : "fixed bottom-6 right-6 rounded-full bg-slate-900 px-6 py-3 text-sm font-semibold text-white shadow-lg hover:bg-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-slate-400/70"
    }
  >
    Design wechseln · {theme === "corsair" ? "Legacy" : "Corsair 3.0"}
  </button>
);

const Logo: React.FC<{ theme: Theme }> = ({ theme }) => (
  <div
    className={
      theme === "corsair"
        ? "flex h-10 w-16 items-center justify-center rounded-xl border border-white/15 bg-white/5"
        : "flex h-10 w-16 items-center justify-center rounded-xl border border-slate-200 bg-white"
    }
  >
    {/* Replace with: <img src={CorsairLogo} alt="Corsair Logo" className="h-4 opacity-80" /> */}
    <svg
      viewBox="0 0 63 11"
      className={theme === "corsair" ? "h-4 w-auto opacity-80" : "h-4 w-auto opacity-80 text-slate-900"}
      fill={theme === "corsair" ? "white" : "currentColor"}
      aria-hidden
    >
      <path d="M4.448 9.713c-.601.71-1.326 1.055-2.175 1.035-.79-.01-1.384-.285-1.784-.826-.4-.541-.555-1.266-.465-2.175l.87-5.213h2.45L2.46 7.783c-.015.145-.015.277 0 .396.035.407.276.618.723.633.516.02.956-.184 1.318-.611l.998-5.667h2.465L6.563 10.59H4.284l.164-.878z" />
      <path d="M10.772 2.527l-.164.967c.645-.76 1.43-1.13 2.353-1.11.486.01.886.124 1.199.343.313.22.522.51.626.873.71-.829 1.527-1.234 2.45-1.214.745.015 1.297.295 1.657.838.36.543.491 1.309.391 2.297l-.842 5.072h-2.457l.856-5.073.03-.438c0-.49-.23-.743-.692-.758-.432 0-.834.221-1.206.662l-.976 5.608h-2.457l.849-5.057.03-.446c0-.51-.23-.765-.692-.765-.422 0-.819.221-1.192.662l-.99 5.608H7.093l1.4-8.058h2.279z" />
      <path d="M23.565 8.283c.064-.327-.19-.573-.761-.737l-.528-.134c-.864-.228-1.497-.548-1.899-.96-.402-.412-.59-.901-.565-1.467.025-.774.368-1.403 1.031-1.887.663-.484 1.471-.721 2.424-.711.948.01 1.717.251 2.305.723.588.472.887 1.107.897 1.906H24.027c.02-.635-.26-.953-.841-.953-.249 0-.479.074-.692.22-.213.147-.34.342-.379.585-.085.402.27.677 1.065.826.69.165 1.223.354 1.601.57.378.216.666.483.865.801.199.317.291.7.276 1.146-.015.487-.174.921-.477 1.303-.303.382-.74.688-1.314.916-.574.228-1.195.335-1.865.32-.58-.005-1.12-.127-1.619-.365-.499-.239-.889-.563-1.169-.973-.28-.41-.425-.88-.435-1.41h2.279c.01.715.368 1.068 1.073 1.058.303 0 .562-.068.775-.205.213-.137.348-.329.403-.577z" />
      <path d="M29.847 10.741c-.72-.005-1.362-.175-1.925-.51-.564-.336-.989-.801-1.277-1.4-.288-.598-.402-1.258-.342-1.978l.022-.209c.134-1.326.594-2.374 1.381-3.146.787-.772 1.751-1.142 2.894-1.113.69.01 1.28.185 1.772.526.491.341.851.81 1.079 1.41.228.599.302 1.272.223 2.018l-.141 1.022H28.737c.01.423.129.765.358 1.028.228.263.561.402.997.417.71.02 1.348-.252 1.914-.818l1.027 1.36c-.303.431-.726.769-1.27 1.014-.543.245-1.138.373-1.783.383h-.134zm.596-6.42c-.347-.01-.648.099-.904.326-.255.226-.478.606-.666 1.14h2.45l.043-.215c.03-.173.035-.336.015-.488-.084-.494-.397-.748-.938-.764z" />
      <path d="M37.8.531l-.35 2.003h1.288l-.305 1.937h-1.288l-.625 3.506c-.035.253-.018.444.048.573.067.129.235.198.502.208.104.005.319-.007.641-.037l-.179 1.817c-.412.134-.852.196-1.318.186-.76-.01-1.328-.233-1.706-.67-.378-.437-.532-1.03-.462-1.779l.656-3.804h-.998l.298-1.937h.998l.35-2.003H37.8z" />
      <path d="M41.231 8.64l3.53.015-.335 1.937h-6.658l.261-1.504 4.237-4.602-4.393-.015.335-1.936h7.536l-.254 1.467-4.259 4.638z" />
      <path d="M48.326 10.741c-.72-.005-1.362-.175-1.925-.51-.563-.336-.989-.801-1.277-1.4-.288-.598-.402-1.258-.342-1.978l.022-.209c.134-1.326.594-2.374 1.381-3.146.787-.772 1.751-1.142 2.894-1.113.69.01 1.28.185 1.772.526.491.341.851.81 1.079 1.41.228.599.302 1.272.223 2.018l-.141 1.022h-4.795c.01.423.129.765.358 1.028.228.263.561.402.997.417.71.02 1.348-.252 1.914-.818l1.027 1.36c-.303.431-.726.769-1.27 1.014-.543.245-1.138.373-1.784.383h-.134zm.596-6.42c-.347-.01-.648.099-.904.326-.256.226-.478.606-.666 1.14h2.45l.043-.215c.03-.173.036-.336.015-.488-.085-.494-.398-.748-.939-.764z" />
      <path d="M57.572 4.805c-.263-.04-.516-.064-.759-.074-.735-.02-1.296.233-1.683.76L54.22 10.592h-2.45l1.4-8.058h2.286l-.186 1.057c.526-.814 1.147-1.22 1.862-1.22.204 0 .457.035.76.104l-.32 2.339z" />
      <path d="M61.117 3.948c-.267 0-.515-.048-.743-.144a1.83 1.83 0 01-.599-.4 2.025 2.025 0 01-.4-.598A1.81 1.81 0 0159.232 2c0-.268.048-.515.143-.743.096-.228.229-.427.4-.598.17-.171.37-.305.598-.4A1.81 1.81 0 0161.117.18c.267 0 .515.048.743.143a1.83 1.83 0 01.599.4c.171.171.305.37.4.598.096.228.143.475.143.743 0 .268-.047.515-.143.743a1.83 1.83 0 01-.4.599c-.171.17-.37.304-.599.4-.228.095-.476.143-.743.143zm-.003-.375c.215 0 .413-.038.593-.114.18-.077.337-.183.47-.32.132-.137.235-.297.308-.48.073-.183.11-.381.11-.596 0-.214-.037-.415-.11-.598a1.268 1.268 0 00-.308-.48 1.276 1.276 0 00-.47-.315 1.598 1.598 0 00-.593-.118c-.285 0-.54.066-.763.199a1.28 1.28 0 00-.526.54c-.127.227-.19.484-.19.77 0 .286.063.543.19.77.127.227.302.407.526.54.224.132.478.199.763.199zm-.775-.408V.966h.957c.174 0 .31.033.41.1.1.066.171.15.212.252.042.102.063.205.063.309 0 .135-.039.264-.116.387-.077.123-.198.206-.363.25l.509.899h-.473l-.463-.861h-.304v.861h-.432zm.432-.247h.515c.093 0 .16-.029.2-.086.04-.057.06-.123.06-.196a.38.38 0 00-.023-.121.224.224 0 00-.081-.103.285.285 0 00-.156-.042h-.515v.548z" />
    </svg>
  </div>
);

export default App;

