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
    <div ref={setNodeRef} style={style} className={`watchlist-item-wrapper ${isDragging ? "dragging" : ""} ${isActive ? "active" : ""}`}>
      <div className="drag-handle" {...attributes} {...listeners}>
        <GripVertical size={14} />
      </div>
      <Link href={`/chart/${urlSymbol}`} className="watchlist-item-link">
        <div className="watchlist-left">
          <span className="watchlist-symbol">{symbol.replace("/USDT", "")}</span>
        </div>
        <div className="watchlist-right">
          <span className="watchlist-price">{ticker?.price?.toLocaleString(undefined, { maximumFractionDigits: ticker.price < 1 ? 4 : 2 }) || "—"}</span>
          <span className={`watchlist-change ${(ticker?.change_24h || 0) >= 0 ? "positive" : "negative"}`}>
            {(ticker?.change_24h || 0) >= 0 ? "+" : ""}
            {ticker?.change_24h?.toFixed(2) || "0.00"}%
          </span>
        </div>
      </Link>
      <button className="watchlist-remove" onClick={onRemove} title="Remove from watchlist">
        <X size={14} />
      </button>
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
    </div>
  );
}
