declare module 'vite' {
  export type Plugin = any;
  export function defineConfig(config: any): any;
}

declare module '@vitejs/plugin-react' {
  const plugin: (...args: any[]) => any;
  export default plugin;
}

declare module '@tailwindcss/vite' {
  const plugin: (...args: any[]) => any;
  export default plugin;
}
