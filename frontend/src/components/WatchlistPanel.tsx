"use client";

import { Panel } from "@/components/ui";
import { useWatchlistStore } from "@/stores/watchlistStore";
import { closestCenter, DndContext, DragEndEvent, KeyboardSensor, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Check, GripVertical, Plus, Search, Star, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

interface WatchlistPanelProps {
  currentSymbol?: string;
}

interface TickerData {
  symbol: string;
  price: number;
  change_24h: number;
}

interface SortableItemProps {
  id: string;
  symbol: string;
  ticker?: TickerData;
  isActive: boolean;
  onRemove: (e: React.MouseEvent) => void;
}

function SortableWatchlistItem({ id, symbol, ticker, isActive, onRemove }: SortableItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 10 : 1,
    opacity: isDragging ? 0.5 : 1,
  };

  const urlSymbol = symbol.replace("/", "-");

  return (
    <div ref={setNodeRef} style={style} className={`watchlist-item-wrapper ${isDragging ? "dragging" : ""}`}>
      <div className="drag-handle" {...attributes} {...listeners}>
        <GripVertical size={14} />
      </div>
      <Link href={`/chart/${urlSymbol}`} className={`watchlist-item ${isActive ? "active" : ""}`}>
        <div className="watchlist-left">
          <Star size={12} fill={isActive ? "var(--accent-primary)" : "none"} stroke={isActive ? "var(--accent-primary)" : "currentColor"} />
          <span className="watchlist-symbol">{symbol.replace("/USDT", "")}</span>
        </div>
        <div className="watchlist-right">
          <span className="watchlist-price">{ticker?.price?.toLocaleString(undefined, { maximumFractionDigits: 4 }) || "—"}</span>
          <span className={`watchlist-change ${(ticker?.change_24h || 0) >= 0 ? "positive" : "negative"}`}>{ticker?.change_24h?.toFixed(2) || "0.00"}%</span>
        </div>
        <button className="watchlist-remove" onClick={onRemove} title="Remove from watchlist">
          <X size={12} />
        </button>
      </Link>
    </div>
  );
}

export function WatchlistPanel({ currentSymbol }: WatchlistPanelProps) {
  const { items, removeSymbol, addSymbol, hasSymbol, setItems } = useWatchlistStore();
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [tickerData, setTickerData] = useState<Record<string, TickerData>>({});
  const [allTickers, setAllTickers] = useState<TickerData[]>([]);
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Fetch live prices for watchlist items
  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    async function fetchPrices() {
      try {
        const res = await fetch(`${apiUrl}/api/market/tickers`);
        if (!res.ok) return;
        const data = await res.json();
        const priceMap: Record<string, TickerData> = {};
        const tickers: TickerData[] = [];
        data.tickers?.forEach((t: TickerData) => {
          priceMap[t.symbol] = t;
          tickers.push(t);
        });
        setTickerData(priceMap);
        setAllTickers(tickers);
      } catch (e) {
        console.error("Failed to fetch tickers", e);
      }
    }
    fetchPrices();
    const interval = setInterval(fetchPrices, 10000);
    return () => clearInterval(interval);
  }, []);

  // Close search on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setSearchOpen(false);
        setSearchQuery("");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Focus input when search opens
  useEffect(() => {
    if (searchOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [searchOpen]);

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = items.findIndex((item) => item.symbol === active.id);
      const newIndex = items.findIndex((item) => item.symbol === over.id);

      setItems(arrayMove(items, oldIndex, newIndex));
    }
  }

  // Filter search results
  const searchResults = searchQuery ? allTickers.filter((t) => t.symbol.toLowerCase().includes(searchQuery.toLowerCase())).slice(0, 10) : [];

  const handleAddCoin = (symbol: string) => {
    addSymbol(symbol);
    setSearchQuery("");
    setSearchOpen(false);
  };

  const handleRemoveCoin = (symbol: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    removeSymbol(symbol);
  };

  return (
    <div className="watchlist-container">
      <Panel
        title="Watchlist"
        headerAction={
          <button className="btn btn-ghost btn-sm" onClick={() => setSearchOpen(!searchOpen)} title={searchOpen ? "Close" : "Add coin"}>
            {searchOpen ? <X size={14} /> : <Plus size={14} />}
          </button>
        }
      >
        {/* Search/Add Section */}
        {searchOpen && (
          <div className="search-section" ref={searchRef}>
            <div className="search-input-wrapper">
              <Search size={14} className="search-icon" />
              <input ref={inputRef} className="search-input" placeholder="Search coins..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
            </div>

            {searchQuery && (
              <div className="search-results">
                {searchResults.length === 0 ? (
                  <div className="no-results">No coins found</div>
                ) : (
                  searchResults.map((ticker) => {
                    const inWatchlist = hasSymbol(ticker.symbol);
                    return (
                      <button key={ticker.symbol} className={`search-result-item ${inWatchlist ? "in-watchlist" : ""}`} onClick={() => (inWatchlist ? removeSymbol(ticker.symbol) : handleAddCoin(ticker.symbol))}>
                        <div className="result-left">
                          <span className="result-symbol">{ticker.symbol.replace("/USDT", "")}</span>
                          <span className="result-price">${ticker.price?.toLocaleString(undefined, { maximumFractionDigits: 4 })}</span>
                        </div>
                        <div className="result-right">
                          <span className={`result-change ${(ticker.change_24h || 0) >= 0 ? "positive" : "negative"}`}>{ticker.change_24h?.toFixed(2)}%</span>
                          {inWatchlist ? <Check size={14} className="check-icon" /> : <Plus size={14} className="add-icon" />}
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            )}
          </div>
        )}

        {/* Watchlist Items */}
        <div className="watchlist-items">
          {items.length === 0 ? (
            <div className="empty-state">
              <Star size={24} />
              <p>No coins in watchlist</p>
              <button onClick={() => setSearchOpen(true)}>Add coins</button>
            </div>
          ) : (
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <SortableContext items={items.map((i) => i.symbol)} strategy={verticalListSortingStrategy}>
                {items.map((item) => (
                  <SortableWatchlistItem key={item.symbol} id={item.symbol} symbol={item.symbol} ticker={tickerData[item.symbol]} isActive={currentSymbol === item.symbol} onRemove={(e) => handleRemoveCoin(item.symbol, e)} />
                ))}
              </SortableContext>
            </DndContext>
          )}
        </div>
      </Panel>

      <style jsx>{`
        .watchlist-container {
          display: flex;
          flex-direction: column;
        }

        .search-section {
          padding: 8px;
          border-bottom: 1px solid var(--border-color);
          position: relative;
        }

        .search-input-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          padding: 6px 10px;
        }

        .search-input-wrapper :global(.search-icon) {
          color: var(--text-muted);
          flex-shrink: 0;
        }

        .search-input {
          flex: 1;
          background: transparent;
          border: none;
          color: var(--text-primary);
          font-size: 13px;
          outline: none;
        }

        .search-input::placeholder {
          color: var(--text-muted);
        }

        .search-results {
          position: absolute;
          top: 100%;
          left: 8px;
          right: 8px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          max-height: 300px;
          overflow-y: auto;
          z-index: 100;
        }

        .no-results {
          padding: 16px;
          text-align: center;
          color: var(--text-muted);
          font-size: 12px;
        }

        .search-result-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          width: 100%;
          padding: 10px 12px;
          background: transparent;
          border: none;
          cursor: pointer;
          transition: background 0.1s;
        }

        .search-result-item:hover {
          background: var(--bg-tertiary);
        }

        .search-result-item.in-watchlist {
          background: rgba(79, 70, 229, 0.1);
        }

        .result-left {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .result-symbol {
          font-weight: 600;
          color: var(--text-primary);
          font-size: 13px;
        }

        .result-price {
          font-size: 12px;
          color: var(--text-muted);
        }

        .result-right {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .result-change {
          font-size: 12px;
          font-weight: 600;
        }

        .result-change.positive {
          color: var(--positive);
        }

        .result-change.negative {
          color: var(--negative);
        }

        .result-right :global(.check-icon) {
          color: var(--positive);
        }

        .result-right :global(.add-icon) {
          color: var(--text-muted);
        }

        .watchlist-items {
          flex: 1;
          overflow-y: auto;
          max-height: 360px; /* ~10 items at 36px each */
        }

        .watchlist-item-wrapper {
          display: flex;
          align-items: center;
          padding-left: 4px;
          position: relative;
        }

        .watchlist-item-wrapper:hover {
          background: var(--bg-tertiary);
        }

        .drag-handle {
          color: var(--text-muted);
          cursor: grab;
          padding: 8px 4px;
          display: flex;
          align-items: center;
          opacity: 0;
          transition: opacity 0.1s;
        }

        .watchlist-item-wrapper:hover .drag-handle {
          opacity: 0.5;
        }

        .drag-handle:hover {
          opacity: 1 !important;
        }

        .watchlist-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 8px 12px 8px 4px;
          width: 100%;
          text-decoration: none;
          color: inherit;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 32px 16px;
          gap: 12px;
          color: var(--text-muted);
        }

        .empty-state p {
          margin: 0;
          font-size: 13px;
        }

        .empty-state button {
          background: var(--accent-primary);
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.15s;
        }

        .empty-state button:hover {
          opacity: 0.9;
        }

        .watchlist-left {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .watchlist-symbol {
          font-weight: 600;
          color: var(--text-primary);
          font-size: 13px;
        }

        .watchlist-right {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 2px;
          margin-left: auto;
          margin-right: 8px;
        }

        .watchlist-price {
          font-size: 13px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .watchlist-change {
          font-size: 11px;
          font-weight: 600;
        }

        .watchlist-change.positive {
          color: var(--positive);
        }

        .watchlist-change.negative {
          color: var(--negative);
        }

        .watchlist-remove {
          opacity: 0;
          background: none;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          transition: all 0.1s;
        }

        .watchlist-remove:hover {
          color: var(--negative);
          background: rgba(239, 68, 68, 0.1);
        }

        .watchlist-item-wrapper:hover .watchlist-remove {
          opacity: 1;
        }

        .watchlist-item.active {
          background: rgba(79, 70, 229, 0.05);
        }
      `}</style>
    </div>
  );
}
