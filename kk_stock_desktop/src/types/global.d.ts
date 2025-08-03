// 全局类型声明文件

// Vue 3 类型声明
declare module 'vue' {
  export function ref<T>(value: T): Ref<T>
  export function computed<T>(getter: () => T): ComputedRef<T>
  export function computed<T>(options: { get: () => T; set: (value: T) => void }): WritableComputedRef<T>
  export function onMounted(fn: () => void): void
  export function onUnmounted(fn: () => void): void
  export function onBeforeMount(fn: () => void): void
  export function onBeforeUnmount(fn: () => void): void
  export function nextTick(fn?: () => void): Promise<void>
  export function watch<T>(source: () => T, cb: (newVal: T, oldVal: T) => void, options?: any): void
  export function watch<T>(source: T, cb: (newVal: T, oldVal: T) => void, options?: any): void
  export function shallowRef<T>(value: T): Ref<T>
  export function reactive<T extends object>(obj: T): T
  export function withDefaults<T>(props: T, defaults: any): T
  export function defineProps<T>(): T
  export function defineEmits<T = any>(emitOptions?: T): (event: string, ...args: any[]) => void
  export function getCurrentInstance(): any
  
  export interface Ref<T> {
    value: T
  }
  
  export interface ComputedRef<T> {
    readonly value: T
  }
  
  export interface WritableComputedRef<T> {
    value: T
  }
  
  export type Ref = any
  export type PropType<T> = any
  
  // 其他Vue3 API
  export * from '@vue/runtime-core'
  export * from '@vue/reactivity'
  export * from '@vue/shared'
}

// Element Plus 类型声明
declare module 'element-plus' {
  export const ElRadioGroup: any
  export const ElRadioButton: any
  export const ElSelect: any
  export const ElOption: any
  export const ElButton: any
  export const ElIcon: any
  export const ElMessage: any
  export const ElLoading: any
  export const ElNotification: any
  export const ElMessageBox: any
  export const ElDialog: any
  export const ElForm: any
  export const ElFormItem: any
  
  export interface ElFormInstance {
    validate(): Promise<boolean>
    clearValidate(): void
    resetFields(): void
  }
  export const ElInput: any
  export const ElCheckbox: any
  export const ElDatePicker: any
  export const ElTimePicker: any
  export const ElTable: any
  export const ElTableColumn: any
  export const ElPagination: any
  export const ElCard: any
  export const ElTabs: any
  export const ElTabPane: any
  export const ElCollapse: any
  export const ElCollapseItem: any
  export const ElTooltip: any
  export const ElPopover: any
  export const ElDropdown: any
  export const ElDropdownMenu: any
  export const ElDropdownItem: any
  export const ElMenu: any
  export const ElMenuItem: any
  export const ElSubMenu: any
  export const ElBreadcrumb: any
  export const ElBreadcrumbItem: any
  export const ElAlert: any
  export const ElTag: any
  export const ElBadge: any
  export const ElProgress: any
  export const ElSwitch: any
  export const ElSlider: any
  export const ElRate: any
  export const ElColorPicker: any
  export const ElTransfer: any
  export const ElTree: any
  export const ElUpload: any
  export const ElAvatar: any
  export const ElEmpty: any
  export const ElDescriptions: any
  export const ElDescriptionsItem: any
  export const ElResult: any
  export const ElSkeleton: any
  export const ElSkeletonItem: any
  export const ElAffix: any
  export const ElAnchor: any
  export const ElAnchorLink: any
  export const ElBackTop: any
  export const ElConfigProvider: any
  export const ElSpace: any
  export const ElDivider: any
  
  export type ElRadioGroupProps = any
  export type ElSelectProps = any
  export type ElButtonProps = any
  
  // 导出所有组件
  export * from 'element-plus/es'
}

// Element Plus Icons
declare module '@element-plus/icons-vue' {
  export const Loading: any
  export const Warning: any
  export const Success: any
  export const Error: any
  export const Info: any
  export const Close: any
  export const Check: any
  export const Plus: any
  export const Minus: any
  export const Edit: any
  export const Delete: any
  export const Search: any
  export const Refresh: any
  export const ChatDotRound: any
  export const User: any
  export const UserFilled: any
  export const Setting: any
  export const InfoFilled: any
  export const TrendCharts: any
  export const TrendingUp: any
  export const EllipsisHorizontalIcon: any
  export const EllipsisVerticalIcon: any
  export const Bars3Icon: any
  export const FolderIcon: any
  export const PlusIcon: any
  export const ArrowPathIcon: any
  export const Lock: any
  export const Unlock: any
  export const View: any
  export const Hide: any
  export const ArrowLeft: any
  export const ArrowRight: any
  export const ArrowUp: any
  export const ArrowDown: any
  export const Download: any
  export const Upload: any
  export const Share: any
  export const Star: any
  export const Heart: any
  export const Message: any
  export const Phone: any
  export const Location: any
  export const Time: any
  export const Calendar: any
  export const Document: any
  export const Folder: any
  export const Picture: any
  export const Video: any
  export const Headphone: any
  export const Camera: any
  export const Microphone: any
  export const House: any
  export const Shop: any
  export const School: any
  export const Office: any
  export const Hospital: any
  export const Restaurant: any
  
  // 导出所有图标
  export * from '@element-plus/icons-vue'
}

// Heroicons
declare module '@heroicons/vue/24/outline' {
  export const ChartBarIcon: any
  export const ChartLineIcon: any
  export const ChartPieIcon: any
  export const DocumentTextIcon: any
  export const CogIcon: any
  export const UserIcon: any
  export const HomeIcon: any
  export const BellIcon: any
  export const MagnifyingGlassIcon: any
  export const PlusIcon: any
  export const MinusIcon: any
  export const XMarkIcon: any
  export const CheckIcon: any
  export const ExclamationTriangleIcon: any
  export const InformationCircleIcon: any
  export const QuestionMarkCircleIcon: any
  export const ArrowLeftIcon: any
  export const ArrowRightIcon: any
  export const ArrowUpIcon: any
  export const ArrowDownIcon: any
  export const ChevronLeftIcon: any
  export const ChevronRightIcon: any
  export const ChevronUpIcon: any
  export const ChevronDownIcon: any
  export const EyeIcon: any
  export const EyeSlashIcon: any
  export const CogIcon: any
  export const ScaleIcon: any
  export const BoltIcon: any
  export const CurrencyDollarIcon: any
  export const ShieldCheckIcon: any
  export const InformationCircleIcon: any
  export const PencilIcon: any
  export const TrashIcon: any
  export const DocumentIcon: any
  export const FolderIcon: any
  export const PhotoIcon: any
  export const VideoCameraIcon: any
  export const MusicalNoteIcon: any
  export const CalendarIcon: any
  export const ClockIcon: any
  export const MapPinIcon: any
  export const PhoneIcon: any
  export const EnvelopeIcon: any
  export const ShareIcon: any
  export const HeartIcon: any
  export const StarIcon: any
  export const BookmarkIcon: any
  export const TagIcon: any
  export const FlagIcon: any
  export const LightBulbIcon: any
  export const FireIcon: any
  export const BoltIcon: any
  export const ShieldCheckIcon: any
  export const LockClosedIcon: any
  export const LockOpenIcon: any
  export const KeyIcon: any
  export const CreditCardIcon: any
  export const BanknotesIcon: any
  export const CalculatorIcon: any
  export const ScaleIcon: any
  export const TrophyIcon: any
  export const AcademicCapIcon: any
  export const BeakerIcon: any
  export const CpuChipIcon: any
  export const ServerIcon: any
  export const CloudIcon: any
  export const WifiIcon: any
  export const SignalIcon: any
  export const DevicePhoneMobileIcon: any
  export const ComputerDesktopIcon: any
  export const PrinterIcon: any
  export const CameraIcon: any
  export const MicrophoneIcon: any
  export const SpeakerWaveIcon: any
  export const PlayIcon: any
  export const PauseIcon: any
  export const StopIcon: any
  export const ForwardIcon: any
  export const BackwardIcon: any
  export const LanguageIcon: any
  export const GlobeAltIcon: any
  export const MapIcon: any
  export const BuildingOfficeIcon: any
  export const HomeModernIcon: any
  export const BuildingStorefrontIcon: any
  export const TruckIcon: any
  export const CarIcon: any
  export const RocketLaunchIcon: any
  export const ArrowPathIcon: any
  export const TrendingUpIcon: any
  export const TrendingDownIcon: any
  export const CurrencyDollarIcon: any
  export const ListBulletIcon: any
  export const UserGroupIcon: any
  
  // 导出所有图标
  export * from '@heroicons/vue/24/outline'
}

// ECharts 类型声明
declare module 'echarts' {
  export function init(dom: HTMLElement | null, theme?: any, opts?: any): any
  export function dispose(chart: any): void
  export function getInstanceByDom(dom: HTMLElement): any
  export function registerTheme(name: string, theme: any): void
  export function registerMap(mapName: string, geoJson: any, specialAreas?: any): void
  export function graphic(): any
  export function util(): any
  export const version: string
  
  export interface ECharts {
    setOption(option: any, notMerge?: boolean, lazyUpdate?: boolean): void
    resize(opts?: any): void
    dispose(): void
    isDisposed(): boolean
    clear(): void
    on(eventName: string, handler: (...args: any[]) => void): void
    off(eventName: string, handler?: (...args: any[]) => void): void
    dispatchAction(payload: any): void
    getOption(): any
    getWidth(): number
    getHeight(): number
    getZr(): any
    getModel(): any
    getViewOfComponentModel(componentModel: any): any
    getViewOfSeriesModel(seriesModel: any): any
  }
  
  export namespace graphic {
    export class LinearGradient {
      constructor(x: number, y: number, x2: number, y2: number, colorStops: Array<{offset: number, color: string}>): any
    }
  }
  
  export * from 'echarts/lib/echarts'
}

// 其他常用库的类型声明
declare module 'lodash' {
  export function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait?: number,
    options?: any
  ): T
  export function throttle<T extends (...args: any[]) => any>(
    func: T,
    wait?: number,
    options?: any
  ): T
  export function cloneDeep<T>(value: T): T
  export function isEqual(value: any, other: any): boolean
  export function merge<T>(object: T, ...sources: any[]): T
  export function pick<T, K extends keyof T>(object: T, ...props: K[]): Pick<T, K>
  export function omit<T, K extends keyof T>(object: T, ...props: K[]): Omit<T, K>
  export * from 'lodash'
}

declare module 'dayjs' {
  interface Dayjs {
    format(template?: string): string
    add(value: number, unit: string): Dayjs
    subtract(value: number, unit: string): Dayjs
    isBefore(date: any): boolean
    isAfter(date: any): boolean
    isSame(date: any): boolean
    valueOf(): number
    unix(): number
    toDate(): Date
    toISOString(): string
  }
  
  interface DayjsStatic {
    (date?: any): Dayjs
    extend(plugin: any): DayjsStatic
    locale(preset: string, object?: any): string
    isDayjs(d: any): d is Dayjs
    unix(timestamp: number): Dayjs
  }
  
  const dayjs: DayjsStatic
  export = dayjs
}

declare module 'axios' {
  export interface AxiosRequestConfig {
    url?: string
    method?: string
    baseURL?: string
    transformRequest?: any
    transformResponse?: any
    headers?: any
    params?: any
    paramsSerializer?: any
    data?: any
    timeout?: number
    timeoutErrorMessage?: string
    withCredentials?: boolean
    adapter?: any
    auth?: any
    responseType?: string
    responseEncoding?: string
    xsrfCookieName?: string
    xsrfHeaderName?: string
    onUploadProgress?: any
    onDownloadProgress?: any
    maxContentLength?: number
    validateStatus?: any
    maxBodyLength?: number
    maxRedirects?: number
    socketPath?: string
    httpAgent?: any
    httpsAgent?: any
    proxy?: any
    cancelToken?: any
    decompress?: boolean
    signal?: AbortSignal
  }
  
  export interface AxiosResponse<T = any> {
    data: T
    status: number
    statusText: string
    headers: any
    config: AxiosRequestConfig
    request?: any
  }
  
  export interface AxiosInstance {
    (config: AxiosRequestConfig): Promise<AxiosResponse>
    (url: string, config?: AxiosRequestConfig): Promise<AxiosResponse>
    defaults: AxiosRequestConfig
    interceptors: {
      request: any
      response: any
    }
    get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
    delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
    head<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
    options<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
    post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
    put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
    patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
  }
  
  const axios: AxiosInstance
  export default axios
  export function create(config?: AxiosRequestConfig): AxiosInstance
}

// CSS模块声明
declare module '*.css' {
  const content: any
  export default content
}

declare module '*.scss' {
  const content: any
  export default content
}

declare module '*.sass' {
  const content: any
  export default content
}

declare module '*.less' {
  const content: any
  export default content
}

declare module '*.styl' {
  const content: any
  export default content
}

// 图片和媒体文件声明
declare module '*.png' {
  const content: string
  export default content
}

declare module '*.jpg' {
  const content: string
  export default content
}

declare module '*.jpeg' {
  const content: string
  export default content
}

declare module '*.gif' {
  const content: string
  export default content
}

declare module '*.svg' {
  const content: string
  export default content
}

declare module '*.ico' {
  const content: string
  export default content
}

declare module '*.webp' {
  const content: string
  export default content
}

declare module '*.mp4' {
  const content: string
  export default content
}

declare module '*.webm' {
  const content: string
  export default content
}

declare module '*.ogg' {
  const content: string
  export default content
}

declare module '*.mp3' {
  const content: string
  export default content
}

declare module '*.wav' {
  const content: string
  export default content
}

declare module '*.flac' {
  const content: string
  export default content
}

declare module '*.aac' {
  const content: string
  export default content
}

// JSON文件声明
declare module '*.json' {
  const content: any
  export default content
}

// 其他文件格式声明
declare module '*.txt' {
  const content: string
  export default content
}

declare module '*.md' {
  const content: string
  export default content
}

declare module '*.pdf' {
  const content: string
  export default content
}

declare module '*.doc' {
  const content: string
  export default content
}

declare module '*.docx' {
  const content: string
  export default content
}

declare module '*.xls' {
  const content: string
  export default content
}

declare module '*.xlsx' {
  const content: string
  export default content
}

declare module '*.zip' {
  const content: string
  export default content
}

declare module '*.rar' {
  const content: string
  export default content
}

declare module '*.7z' {
  const content: string
  export default content
}

// 字体文件声明
declare module '*.woff' {
  const content: string
  export default content
}

declare module '*.woff2' {
  const content: string
  export default content
}

declare module '*.eot' {
  const content: string
  export default content
}

declare module '*.ttf' {
  const content: string
  export default content
}

declare module '*.otf' {
  const content: string
  export default content
}

// 环境变量声明
declare interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_VERSION: string
  readonly VITE_BUILD_TIME: string
  readonly MODE: string
  readonly BASE_URL: string
  readonly PROD: boolean
  readonly DEV: boolean
  readonly SSR: boolean
}

declare interface ImportMeta {
  readonly env: ImportMetaEnv
}

// 全局变量声明
declare interface Window {
  __VUE_DEVTOOLS_GLOBAL_HOOK__: any
  __VUE_OPTIONS_API__: boolean
  __VUE_PROD_DEVTOOLS__: boolean
  __INTLIFY_JIT_COMPILATION__: boolean
  __INTLIFY_PROD_DEVTOOLS__: boolean
  electronAPI: any
}

// Node.js 全局变量
declare const process: {
  env: {
    NODE_ENV: string
    [key: string]: string | undefined
  }
  platform: string
  argv: string[]
  cwd(): string
  nextTick(callback: () => void): void
}

declare const global: typeof globalThis

// 浏览器 API 增强
declare interface Navigator {
  userAgentData?: {
    brands: Array<{
      brand: string
      version: string
    }>
    mobile: boolean
    platform: string
  }
}

// CSS 自定义属性
declare module 'csstype' {
  interface Properties {
    [index: `--${string}`]: any
  }
}

// Marked.js 模块声明
declare module 'marked' {
  export interface MarkedOptions {
    breaks?: boolean
    gfm?: boolean
    headerIds?: boolean
    headerPrefix?: string
    highlight?: (code: string, lang: string) => string
    langPrefix?: string
    mangle?: boolean
    pedantic?: boolean
    sanitize?: boolean
    sanitizer?: (text: string) => string
    silent?: boolean
    smartLists?: boolean
    smartypants?: boolean
    tables?: boolean
    xhtml?: boolean
  }

  export interface Marked {
    parse(src: string, options?: MarkedOptions): string
    parseInline(src: string, options?: MarkedOptions): string
    use(extension: any): Marked
    setOptions(options: MarkedOptions): Marked
    getDefaults(): MarkedOptions
  }

  export const marked: Marked
  export default marked
}

// Vue ECharts 模块声明
declare module 'vue-echarts' {
  import { DefineComponent } from 'vue'
  const VChart: DefineComponent<{
    option?: any
    initOptions?: any
    loading?: boolean
    loadingOptions?: any
    style?: any
    autoresize?: boolean
  }>
  export default VChart
}