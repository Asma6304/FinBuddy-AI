"use client";

import { useRef, useEffect, useState } from "react";
import { Camera, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import useFetch from "@/hooks/use-fetch";
import { scanReceipt } from "@/actions/transaction";

export function ReceiptScanner({ onScanComplete }) {
  const fileInputRef = useRef(null);

  const [scanReceiptLoading, setScanReceiptLoading] = useState(false);

  const handleReceiptScan = async (file) => {
    console.log("handleReceiptScan called with file:", file.name);
    if (file.size > 5 * 1024 * 1024) {
      toast.error("File size should be less than 5MB");
      return;
    }

    setScanReceiptLoading(true);
    try {
      console.log("Calling scanReceipt directly...");

      const formData = new FormData();
      formData.append("file", file);

      const data = await scanReceipt(formData);
      console.log("Scan result:", data);
      onScanComplete(data);
      toast.success("Receipt scanned successfully");
    } catch (error) {
      console.error("Scan error:", error);
      toast.error(error.message || "Failed to scan receipt");
    } finally {
      setScanReceiptLoading(false);
    }
  };

  /*
  const {
    loading: scanReceiptLoading,
    fn: scanReceiptFn,
    data: scannedData,
  } = useFetch(scanReceipt);

  useEffect(() => {
    console.log("ReceiptScanner Effect:", { scannedData, scanReceiptLoading });
    if (scannedData && !scanReceiptLoading) {
      onScanComplete(scannedData);
      toast.success("Receipt scanned successfully");
    }
  }, [scanReceiptLoading, scannedData]);
  */

  return (
    <div className="flex items-center gap-4">
      <input
        type="file"
        ref={fileInputRef}
        className="" // Removed hidden for debugging
        accept="image/*"
        capture="environment"
        onChange={(e) => {
          const file = e.target.files?.[0];
          console.log("File selected:", file);
          if (file) handleReceiptScan(file);
        }}
      />
      <Button
        type="button"
        variant="outline"
        className="w-full h-10 bg-gradient-to-br from-orange-500 via-pink-500 to-purple-500 animate-gradient hover:opacity-90 transition-opacity text-white hover:text-white"
        onClick={() => {
          console.log("Button clicked");
          fileInputRef.current?.click();
        }}
        disabled={scanReceiptLoading}
      >
        {scanReceiptLoading ? (
          <>
            <Loader2 className="mr-2 animate-spin" />
            <span>Scanning Receipt...</span>
          </>
        ) : (
          <>
            <Camera className="mr-2" />
            <span>Scan Receipt with AI</span>
          </>
        )}
      </Button>
    </div>
  );
}
