import { useRef, useEffect, useState, useCallback } from 'react';
import {
  Square, Circle, Type, Minus, Triangle, Move, Trash2,
  Download, ZoomIn, ZoomOut, Copy, Scissors, Printer
} from 'lucide-react';
import PageHeader from '../components/PageHeader';

type ToolType = 'select' | 'rect' | 'circle' | 'text' | 'line' | 'triangle' | 'cut-contour';
type LayerType = 'print' | 'cut' | 'both';

interface DesignElement {
  id: string;
  type: 'rect' | 'circle' | 'text' | 'line' | 'triangle';
  x: number;
  y: number;
  width: number;
  height: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
  layer: LayerType;
  text?: string;
  fontSize?: number;
  selected?: boolean;
  rotation?: number;
}

const CANVAS_W = 600;
const CANVAS_H = 500;

const defaultColors = ['#000000', '#FFFFFF', '#FF0000', '#00AA00', '#0000FF', '#FFFF00', '#FF6600', '#9900CC', '#00CCCC'];

export default function DesignCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tool, setTool] = useState<ToolType>('select');
  const [elements, setElements] = useState<DesignElement[]>([
    { id: '1', type: 'rect', x: 100, y: 100, width: 200, height: 120, fill: '#6366f1', stroke: '#4338ca', strokeWidth: 2, layer: 'both' },
    { id: '2', type: 'circle', x: 350, y: 150, width: 100, height: 100, fill: '#f59e0b', stroke: '#d97706', strokeWidth: 2, layer: 'print' },
    { id: '3', type: 'text', x: 130, y: 145, width: 150, height: 30, fill: '#FFFFFF', stroke: 'transparent', strokeWidth: 0, layer: 'print', text: 'نص تجريبي', fontSize: 22 },
  ]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [fillColor, setFillColor] = useState('#6366f1');
  const [strokeColor, setStrokeColor] = useState('#000000');
  const [strokeWidth, setStrokeWidth] = useState(2);
  const [activeLayer, setActiveLayer] = useState<LayerType>('both');
  const [showCutContour, setShowCutContour] = useState(true);
  const [canvasSize, setCanvasSize] = useState({ w: 100, h: 100, unit: 'mm' });
  const [zoom, setZoom] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const selectedEl = elements.find((e) => e.id === selectedId);

  const redraw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);

    // Background
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

    // Grid
    ctx.strokeStyle = '#f0f0f0';
    ctx.lineWidth = 1;
    for (let x = 0; x < CANVAS_W; x += 20) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, CANVAS_H); ctx.stroke();
    }
    for (let y = 0; y < CANVAS_H; y += 20) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(CANVAS_W, y); ctx.stroke();
    }

    // Draw elements
    elements.forEach((el) => {
      ctx.save();
      ctx.translate(el.x + el.width / 2, el.y + el.height / 2);
      if (el.rotation) ctx.rotate((el.rotation * Math.PI) / 180);
      ctx.translate(-(el.width / 2), -(el.height / 2));

      ctx.fillStyle = el.fill;
      ctx.strokeStyle = el.stroke;
      ctx.lineWidth = el.strokeWidth;

      if (el.type === 'rect') {
        ctx.fillRect(0, 0, el.width, el.height);
        if (el.strokeWidth > 0) ctx.strokeRect(0, 0, el.width, el.height);
      } else if (el.type === 'circle') {
        ctx.beginPath();
        ctx.ellipse(el.width / 2, el.height / 2, el.width / 2, el.height / 2, 0, 0, Math.PI * 2);
        ctx.fill();
        if (el.strokeWidth > 0) ctx.stroke();
      } else if (el.type === 'text') {
        ctx.font = `bold ${el.fontSize ?? 20}px Arial`;
        ctx.fillText(el.text ?? '', 0, el.fontSize ?? 20);
      } else if (el.type === 'line') {
        ctx.beginPath();
        ctx.moveTo(0, el.height / 2);
        ctx.lineTo(el.width, el.height / 2);
        ctx.strokeStyle = el.fill;
        ctx.lineWidth = el.strokeWidth || 2;
        ctx.stroke();
      } else if (el.type === 'triangle') {
        ctx.beginPath();
        ctx.moveTo(el.width / 2, 0);
        ctx.lineTo(el.width, el.height);
        ctx.lineTo(0, el.height);
        ctx.closePath();
        ctx.fill();
        if (el.strokeWidth > 0) ctx.stroke();
      }

      // Cut contour overlay
      if (showCutContour && (el.layer === 'cut' || el.layer === 'both')) {
        ctx.strokeStyle = '#ff0066';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        if (el.type === 'circle') {
          ctx.beginPath();
          ctx.ellipse(el.width / 2, el.height / 2, el.width / 2 + 4, el.height / 2 + 4, 0, 0, Math.PI * 2);
          ctx.stroke();
        } else {
          ctx.strokeRect(-4, -4, el.width + 8, el.height + 8);
        }
        ctx.setLineDash([]);
      }

      ctx.restore();

      // Selection handles
      if (el.id === selectedId) {
        ctx.save();
        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 3]);
        ctx.strokeRect(el.x - 2, el.y - 2, el.width + 4, el.height + 4);
        ctx.setLineDash([]);
        // Corner handles
        [[el.x, el.y], [el.x + el.width, el.y], [el.x, el.y + el.height], [el.x + el.width, el.y + el.height]].forEach(([hx, hy]) => {
          ctx.fillStyle = '#6366f1';
          ctx.fillRect(hx - 4, hy - 4, 8, 8);
        });
        ctx.restore();
      }
    });

    // Registration marks in corners
    const markOffset = 20;
    const markSize = 15;
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 1;
    [
      [markOffset, markOffset],
      [CANVAS_W - markOffset, markOffset],
      [markOffset, CANVAS_H - markOffset],
      [CANVAS_W - markOffset, CANVAS_H - markOffset],
    ].forEach(([mx, my]) => {
      ctx.beginPath(); ctx.moveTo(mx - markSize / 2, my); ctx.lineTo(mx + markSize / 2, my); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(mx, my - markSize / 2); ctx.lineTo(mx, my + markSize / 2); ctx.stroke();
      ctx.beginPath(); ctx.arc(mx, my, markSize / 3, 0, Math.PI * 2); ctx.stroke();
    });
  }, [elements, selectedId, showCutContour]);

  useEffect(() => { redraw(); }, [redraw]);

  const getElAtPos = (x: number, y: number) => {
    for (let i = elements.length - 1; i >= 0; i--) {
      const el = elements[i];
      if (x >= el.x && x <= el.x + el.width && y >= el.y && y <= el.y + el.height) return el;
    }
    return null;
  };

  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoom;
    const y = (e.clientY - rect.top) / zoom;

    if (tool === 'select') {
      const el = getElAtPos(x, y);
      if (el) {
        setSelectedId(el.id);
        setDragStart({ x: x - el.x, y: y - el.y });
        setIsDragging(true);
      } else {
        setSelectedId(null);
      }
    } else {
      const id = Math.random().toString(36).slice(2, 9);
      let newEl: DesignElement;

      if (tool === 'text') {
        const text = prompt('أدخل النص:') || 'نص';
        newEl = { id, type: 'text', x, y, width: text.length * 12, height: 30, fill: fillColor, stroke: strokeColor, strokeWidth, layer: activeLayer, text, fontSize: 20 };
      } else if (tool === 'cut-contour') {
        const el = getElAtPos(x, y);
        if (el) {
          setElements((prev) => prev.map((e) => e.id === el.id ? { ...e, layer: 'both' } : e));
        }
        return;
      } else {
        newEl = {
          id, type: tool as any, x, y,
          width: tool === 'line' ? 100 : 80,
          height: tool === 'line' ? 0 : 80,
          fill: fillColor, stroke: strokeColor, strokeWidth, layer: activeLayer
        };
      }
      setElements((prev) => [...prev, newEl]);
      setSelectedId(id);
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging || !selectedId) return;
    const rect = canvasRef.current!.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoom;
    const y = (e.clientY - rect.top) / zoom;
    setElements((prev) =>
      prev.map((el) => el.id === selectedId ? { ...el, x: x - dragStart.x, y: y - dragStart.y } : el)
    );
  };

  const handleCanvasMouseUp = () => setIsDragging(false);

  const deleteSelected = () => {
    if (selectedId) {
      setElements((prev) => prev.filter((e) => e.id !== selectedId));
      setSelectedId(null);
    }
  };

  const duplicateSelected = () => {
    if (selectedId) {
      const el = elements.find((e) => e.id === selectedId);
      if (el) setElements((prev) => [...prev, { ...el, id: Math.random().toString(36).slice(2, 9), x: el.x + 20, y: el.y + 20 }]);
    }
  };

  const updateSelected = (update: Partial<DesignElement>) => {
    if (selectedId) setElements((prev) => prev.map((e) => e.id === selectedId ? { ...e, ...update } : e));
  };

  const downloadCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const a = document.createElement('a');
    a.download = 'design.png';
    a.href = canvas.toDataURL('image/png');
    a.click();
  };

  const tools = [
    { id: 'select', icon: Move, label: 'تحديد' },
    { id: 'rect', icon: Square, label: 'مستطيل' },
    { id: 'circle', icon: Circle, label: 'دائرة' },
    { id: 'triangle', icon: Triangle, label: 'مثلث' },
    { id: 'line', icon: Minus, label: 'خط' },
    { id: 'text', icon: Type, label: 'نص' },
    { id: 'cut-contour', icon: Scissors, label: 'خط قص' },
  ];

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="بيئة التصميم"
        subtitle="صمم ملصقاتك وإضافة خطوط القص"
        actions={
          <div className="flex items-center gap-2">
            <button onClick={downloadCanvas} className="flex items-center gap-1.5 text-sm text-gray-700 bg-white border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50">
              <Download size={14} /> تصدير PNG
            </button>
            <button className="flex items-center gap-1.5 text-sm text-white bg-indigo-600 px-3 py-1.5 rounded-lg hover:bg-indigo-700">
              <Printer size={14} /> إرسال للطباعة
            </button>
          </div>
        }
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Tools Panel */}
        <div className="w-14 bg-white border-l border-gray-200 flex flex-col items-center py-3 gap-1">
          {tools.map((t) => (
            <button
              key={t.id}
              title={t.label}
              onClick={() => setTool(t.id as ToolType)}
              className={`w-10 h-10 flex items-center justify-center rounded-lg transition-colors ${tool === t.id ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:bg-gray-100'}`}
            >
              <t.icon size={16} />
            </button>
          ))}
          <div className="border-t border-gray-200 my-2 w-8" />
          <button title="حذف" onClick={deleteSelected} disabled={!selectedId} className="w-10 h-10 flex items-center justify-center rounded-lg text-gray-400 hover:bg-red-50 hover:text-red-500 disabled:opacity-30">
            <Trash2 size={16} />
          </button>
          <button title="نسخ" onClick={duplicateSelected} disabled={!selectedId} className="w-10 h-10 flex items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 disabled:opacity-30">
            <Copy size={16} />
          </button>
        </div>

        {/* Canvas Area */}
        <div className="flex-1 bg-gray-200 overflow-auto flex items-center justify-center p-8">
          <div style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}>
            <canvas
              ref={canvasRef}
              width={CANVAS_W}
              height={CANVAS_H}
              onMouseDown={handleCanvasMouseDown}
              onMouseMove={handleCanvasMouseMove}
              onMouseUp={handleCanvasMouseUp}
              className="shadow-2xl cursor-crosshair"
              style={{ cursor: tool === 'select' ? (isDragging ? 'grabbing' : 'default') : 'crosshair' }}
            />
          </div>
        </div>

        {/* Properties Panel */}
        <div className="w-56 bg-white border-r border-gray-200 overflow-y-auto">
          {/* Zoom */}
          <div className="p-3 border-b border-gray-100">
            <div className="text-xs font-medium text-gray-700 mb-2">التكبير</div>
            <div className="flex items-center gap-2">
              <button onClick={() => setZoom((z) => Math.max(0.3, z - 0.1))} className="w-7 h-7 bg-gray-100 rounded flex items-center justify-center hover:bg-gray-200">
                <ZoomOut size={12} />
              </button>
              <span className="text-xs flex-1 text-center">{Math.round(zoom * 100)}%</span>
              <button onClick={() => setZoom((z) => Math.min(3, z + 0.1))} className="w-7 h-7 bg-gray-100 rounded flex items-center justify-center hover:bg-gray-200">
                <ZoomIn size={12} />
              </button>
            </div>
          </div>

          {/* Canvas Size */}
          <div className="p-3 border-b border-gray-100">
            <div className="text-xs font-medium text-gray-700 mb-2">حجم اللوحة (مم)</div>
            <div className="flex gap-2">
              <input type="number" value={canvasSize.w} onChange={(e) => setCanvasSize({ ...canvasSize, w: +e.target.value })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500" placeholder="عرض" />
              <input type="number" value={canvasSize.h} onChange={(e) => setCanvasSize({ ...canvasSize, h: +e.target.value })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500" placeholder="ارتفاع" />
            </div>
          </div>

          {/* Layers */}
          <div className="p-3 border-b border-gray-100">
            <div className="text-xs font-medium text-gray-700 mb-2">الطبقة النشطة</div>
            {(['print', 'cut', 'both'] as LayerType[]).map((l) => (
              <button
                key={l}
                onClick={() => setActiveLayer(l)}
                className={`w-full text-right text-xs py-1.5 px-2 rounded mb-1 ${activeLayer === l ? 'bg-indigo-100 text-indigo-700 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
              >
                {l === 'print' ? '🖨 طباعة فقط' : l === 'cut' ? '✂ قص فقط' : '🖨✂ طباعة وقص'}
              </button>
            ))}
            <label className="flex items-center gap-2 mt-2 cursor-pointer">
              <input type="checkbox" checked={showCutContour} onChange={(e) => setShowCutContour(e.target.checked)} className="rounded" />
              <span className="text-xs text-gray-600">إظهار خط القص</span>
            </label>
          </div>

          {/* Fill Color */}
          <div className="p-3 border-b border-gray-100">
            <div className="text-xs font-medium text-gray-700 mb-2">لون التعبئة</div>
            <div className="flex flex-wrap gap-1 mb-2">
              {defaultColors.map((c) => (
                <button
                  key={c}
                  onClick={() => { setFillColor(c); updateSelected({ fill: c }); }}
                  className={`w-6 h-6 rounded border-2 ${fillColor === c ? 'border-indigo-500' : 'border-transparent'}`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
            <input type="color" value={fillColor} onChange={(e) => { setFillColor(e.target.value); updateSelected({ fill: e.target.value }); }}
              className="w-full h-8 rounded border border-gray-300 cursor-pointer" />
          </div>

          {/* Stroke */}
          <div className="p-3 border-b border-gray-100">
            <div className="text-xs font-medium text-gray-700 mb-2">لون الحد</div>
            <input type="color" value={strokeColor} onChange={(e) => { setStrokeColor(e.target.value); updateSelected({ stroke: e.target.value }); }}
              className="w-full h-8 rounded border border-gray-300 cursor-pointer mb-2" />
            <div className="text-xs text-gray-600 mb-1">سماكة الحد</div>
            <input type="range" min="0" max="10" value={strokeWidth} onChange={(e) => { setStrokeWidth(+e.target.value); updateSelected({ strokeWidth: +e.target.value }); }}
              className="w-full" />
          </div>

          {/* Selected Element Properties */}
          {selectedEl && (
            <div className="p-3">
              <div className="text-xs font-medium text-gray-700 mb-2">خصائص العنصر</div>
              <div className="space-y-2">
                <PropInput label="X" value={Math.round(selectedEl.x)} onChange={(v) => updateSelected({ x: v })} />
                <PropInput label="Y" value={Math.round(selectedEl.y)} onChange={(v) => updateSelected({ y: v })} />
                <PropInput label="عرض" value={Math.round(selectedEl.width)} onChange={(v) => updateSelected({ width: v })} />
                <PropInput label="ارتفاع" value={Math.round(selectedEl.height)} onChange={(v) => updateSelected({ height: v })} />
                {selectedEl.type === 'text' && (
                  <PropInput label="حجم الخط" value={selectedEl.fontSize ?? 20} onChange={(v) => updateSelected({ fontSize: v })} />
                )}
                <div>
                  <div className="text-xs text-gray-500 mb-1">الطبقة</div>
                  <select value={selectedEl.layer} onChange={(e) => updateSelected({ layer: e.target.value as LayerType })}
                    className="w-full border border-gray-300 rounded px-2 py-1 text-xs focus:outline-none">
                    <option value="print">طباعة</option>
                    <option value="cut">قص</option>
                    <option value="both">طباعة وقص</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom info bar */}
      <div className="bg-white border-t border-gray-200 px-4 py-2 flex items-center gap-4 text-xs text-gray-500">
        <span>الأداة: {tools.find((t) => t.id === tool)?.label}</span>
        <span>العناصر: {elements.length}</span>
        {selectedEl && <span>محدد: {selectedEl.type} ({Math.round(selectedEl.x)}, {Math.round(selectedEl.y)})</span>}
        <span className="mr-auto flex items-center gap-1">
          <span className="w-3 h-0.5 bg-red-500 inline-block" style={{ borderTop: '1.5px dashed #ff0066' }} />
          خط قص
        </span>
      </div>
    </div>
  );
}

function PropInput({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 w-10 shrink-0">{label}</span>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(+e.target.value)}
        className="flex-1 border border-gray-300 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
      />
    </div>
  );
}
