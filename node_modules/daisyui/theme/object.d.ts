interface Theme {
  "color-scheme": string
  "--color-base-100": string
  "--color-base-200": string
  "--color-base-300": string
  "--color-base-content": string
  "--color-primary": string
  "--color-primary-content": string
  "--color-secondary": string
  "--color-secondary-content": string
  "--color-accent": string
  "--color-accent-content": string
  "--color-neutral": string
  "--color-neutral-content": string
  "--color-info": string
  "--color-info-content": string
  "--color-success": string
  "--color-success-content": string
  "--color-warning": string
  "--color-warning-content": string
  "--color-error": string
  "--color-error-content": string
  "--radius-selector": string
  "--radius-field": string
  "--radius-box": string
  "--size-selector": string
  "--size-field": string
  "--border": string
  "--depth": string
  "--noise": string
}


interface Themes {
  bumblebee: Theme
  retro: Theme
  halloween: Theme
  lofi: Theme
  garden: Theme
  coffee: Theme
  fantasy: Theme
  aqua: Theme
  pastel: Theme
  light: Theme
  synthwave: Theme
  emerald: Theme
  cupcake: Theme
  dark: Theme
  night: Theme
  silk: Theme
  acid: Theme
  business: Theme
  cyberpunk: Theme
  dim: Theme
  nord: Theme
  corporate: Theme
  cmyk: Theme
  valentine: Theme
  abyss: Theme
  wireframe: Theme
  black: Theme
  forest: Theme
  caramellatte: Theme
  lemonade: Theme
  dracula: Theme
  winter: Theme
  sunset: Theme
  luxury: Theme
  autumn: Theme
  [key: string]: Theme
}

declare const themes: Themes
export default themes