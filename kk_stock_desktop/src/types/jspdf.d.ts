// jsPDF 类型定义扩展
declare module 'jspdf' {
  interface jsPDF {
    autoTable: (options: {
      startY?: number
      head?: any[][]
      body?: any[][]
      styles?: any
      headStyles?: any
      bodyStyles?: any
      columnStyles?: any
      didParseCell?: (data: any) => void
      margin?: any
      tableWidth?: string | number
      theme?: string
    }) => jsPDF
    
    getNumberOfPages(): number
    setPage(pageNumber: number): void
    roundedRect(
      x: number, 
      y: number, 
      width: number, 
      height: number, 
      radiusX: number, 
      radiusY: number, 
      style?: string
    ): void
  }
}

declare module 'html2canvas' {
  interface Html2CanvasOptions {
    backgroundColor?: string
    scale?: number
    logging?: boolean
    useCORS?: boolean
    allowTaint?: boolean
    foreignObjectRendering?: boolean
    width?: number
    height?: number
  }

  function html2canvas(
    element: HTMLElement, 
    options?: Html2CanvasOptions
  ): Promise<HTMLCanvasElement>

  export = html2canvas
}

declare module 'jspdf-autotable' {
  // 这个模块主要是扩展 jsPDF 的功能，不需要额外的类型定义
}