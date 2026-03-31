import React from "react";

interface InputProps {
  id?: string;
  type?: string;
  accept?: string;
  className?: string;
  value?: string;
  placeholder?: string;
  disabled?: boolean;
  autoComplete?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function Input({
  id,
  type = "text",
  accept,
  className = "",
  value,
  placeholder,
  disabled,
  autoComplete,
  onChange,
}: InputProps) {
  return (
    <input
      id={id}
      type={type}
      accept={accept}
      value={value}
      placeholder={placeholder}
      disabled={disabled}
      autoComplete={autoComplete}
      onChange={onChange}
      className={`flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm 
      ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium 
      placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 
      focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed 
      disabled:opacity-50 ${className}`}
    />
  );
}