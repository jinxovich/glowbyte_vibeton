import { useCallback, useState } from "react";
import type { UploadDataset } from "../types";

type FileUploadProps = {
  title: string;
  description: string;
  dataset: UploadDataset;
  onUpload: (file: File, dataset: UploadDataset) => Promise<void>;
};

export default function FileUpload({
  title,
  description,
  dataset,
  onUpload,
}: FileUploadProps) {
  const [isDragging, setDragging] = useState(false);
  const [isLoading, setLoading] = useState(false);

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      setLoading(true);
      try {
        await onUpload(files[0], dataset);
      } finally {
        setLoading(false);
      }
    },
    [dataset, onUpload],
  );

  return (
    <div
      onDragEnter={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={(event) => {
        event.preventDefault();
        setDragging(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        handleFiles(event.dataTransfer.files);
      }}
      className={`rounded-2xl border-2 border-dashed p-6 transition-colors ${
        isDragging ? "border-accent bg-accent/10" : "border-slate-800"
      }`}
    >
      <p className="text-sm uppercase tracking-[0.4em] text-slate-400">
        {title}
      </p>
      <p className="mt-3 text-base text-slate-100">{description}</p>

      <label className="mt-6 inline-flex cursor-pointer items-center gap-3 rounded-full bg-primary/30 px-5 py-2 text-sm font-semibold text-white hover:bg-primary/50">
        {isLoading ? "Загрузка..." : "Выберите CSV"}
        <input
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(event) => handleFiles(event.target.files)}
        />
      </label>
    </div>
  );
}

