"use client";

import { Panel } from "@/components/ui";
import { Skeleton } from "@/components/ui/skeleton";
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

import { formatChange, formatPrice } from "@/lib/formatters";
import { cn } from "@/lib/utils";

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
    <div
      ref={setNodeRef}
      style={style}
      className={cn("group flex items-center h-12 border-b border-white/5 transition-colors px-1 relative", isDragging && "bg-muted shadow-lg rounded-lg z-[100]", isActive && "bg-primary/10 border-l-2 border-primary pl-[2.5px]")}
    >
      <div className="flex items-center justify-center w-6 h-full text-muted-foreground cursor-grab opacity-0 group-hover:opacity-40 hover:!opacity-100 transition-opacity" {...attributes} {...listeners}>
        <GripVertical size={14} />
      </div>

      <Link href={`/chart/${urlSymbol}`} className="flex items-center justify-between flex-1 h-full px-2 no-underline text-inherit">
        <div className="flex items-center">
          <span className="font-bold text-[14px] text-foreground tracking-tight">{symbol.replace("/USDT", "")}</span>
        </div>
        <div className="flex flex-col items-end gap-[1px]">
          {ticker ? (
            <>
              <span className="text-[14px] font-semibold text-foreground leading-none">{formatPrice(ticker.price)}</span>
              <span className={cn("text-[11px] font-bold leading-none", ticker.change_24h >= 0 ? "text-success" : "text-danger")}>{formatChange(ticker.change_24h)}</span>
            </>
          ) : (
            <div className="flex flex-col items-end gap-1">
              <Skeleton className="h-[14px] w-16" />
              <Skeleton className="h-[10px] w-10" />
            </div>
          )}
        </div>
      </Link>

      <button
        className="flex items-center justify-center w-7 h-7 p-0 mx-1 bg-transparent border-none text-muted-foreground rounded-md cursor-pointer opacity-0 group-hover/remove:opacity-100 group-hover:opacity-60 hover:!opacity-100 hover:bg-danger/15 hover:text-danger transition-all shrink-0"
        onClick={onRemove}
        title="Remove from watchlist"
      >
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
  const [isMounted, setIsMounted] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

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
    <div className="flex flex-col h-full min-h-0 bg-secondary">
      <Panel
        title="Watchlist"
        headerAction={
          <button className="p-1.5 hover:bg-accent rounded-md text-muted-foreground transition-colors" onClick={() => setSearchOpen(!searchOpen)} title={searchOpen ? "Close" : "Add coin"}>
            {searchOpen ? <X size={14} /> : <Plus size={14} />}
          </button>
        }
      >
        {/* Search/Add Section */}
        {searchOpen && (
          <div className="p-3 border-b border-border relative bg-secondary" ref={searchRef}>
            <div className="flex items-center gap-2 bg-muted border border-border rounded-lg px-3 py-2 transition-all focus-within:border-primary">
              <Search size={14} className="text-muted-foreground shrink-0" />
              <input
                ref={inputRef}
                className="flex-1 bg-transparent border-none text-foreground text-sm outline-none font-medium placeholder:text-muted-foreground"
                placeholder="Search coins..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {searchQuery && (
              <div className="absolute top-full left-3 right-3 bg-secondary border border-border rounded-lg shadow-2xl max-h-60 overflow-y-auto z-[100] mt-1 overflow-x-hidden">
                {searchResults.length === 0 ? (
                  <div className="p-4 text-center text-muted-foreground text-xs font-medium uppercase tracking-wider">No coins found</div>
                ) : (
                  searchResults.map((ticker) => {
                    const inWatchlist = hasSymbol(ticker.symbol);
                    return (
                      <button
                        key={ticker.symbol}
                        className={cn("flex items-center justify-between w-full px-3 py-2.5 transition-colors hover:bg-muted", inWatchlist && "bg-primary/5")}
                        onClick={() => (inWatchlist ? removeSymbol(ticker.symbol) : handleAddCoin(ticker.symbol))}
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-[13px] text-foreground">{ticker.symbol.replace("/USDT", "")}</span>
                          <span className="text-xs text-muted-foreground">${formatPrice(ticker.price)}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={cn("text-xs font-bold", (ticker.change_24h || 0) >= 0 ? "text-success" : "text-danger")}>{formatChange(ticker.change_24h)}</span>
                          {inWatchlist ? <Check size={14} className="text-success" /> : <Plus size={14} className="text-muted-foreground" />}
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
        <div className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-muted">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 px-5 text-center text-muted-foreground">
              <Star size={24} className="opacity-20 mb-3" />
              <p className="text-sm mb-4">No coins in watchlist</p>
              <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg text-xs font-bold hover:opacity-90 transition-opacity" onClick={() => setSearchOpen(true)}>
                Add coins
              </button>
            </div>
          ) : isMounted ? (
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <SortableContext items={items.map((i) => i.symbol)} strategy={verticalListSortingStrategy}>
                <div className="flex flex-col">
                  {items.map((item) => (
                    <SortableWatchlistItem key={item.symbol} id={item.symbol} symbol={item.symbol} ticker={tickerData[item.symbol]} isActive={currentSymbol === item.symbol} onRemove={(e) => handleRemoveCoin(item.symbol, e)} />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          ) : (
            <div className="flex flex-col">
              {items.map((item) => (
                <SortableWatchlistItem key={item.symbol} id={item.symbol} symbol={item.symbol} ticker={tickerData[item.symbol]} isActive={currentSymbol === item.symbol} onRemove={(e) => handleRemoveCoin(item.symbol, e)} />
              ))}
            </div>
          )}
        </div>
      </Panel>
    </div>
  );
}
