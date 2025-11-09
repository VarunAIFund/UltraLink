"use client"

import * as React from "react"
import * as SelectPrimitive from "@radix-ui/react-select"
import { CheckIcon, ChevronDownIcon, ChevronUpIcon } from "lucide-react"

import { cn } from "@/lib/utils"

// Context for multi-select state
const MultiSelectContext = React.createContext<{
  multiple: boolean;
  selectedValues: string[];
  options: Array<{label: string; value: string}>;
  value: string | undefined;
} | null>(null);

function Select({
  multiple,
  value,
  onValueChange,
  children,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Root> & {
  multiple?: boolean;
  options?: Array<{label: string; value: string}>;
}) {
  const [open, setOpen] = React.useState(false);

  // Parse comma-separated value to array
  const selectedValues = React.useMemo(() => {
    if (!value) return [];
    if (value === 'all') return props.options?.map(opt => opt.value) || [];
    return value.split(',').map(v => v.trim().toLowerCase());
  }, [value, props.options]);

  // Handle selection toggle for multi-select
  const handleValueChange = React.useCallback((newValue: string) => {
    console.log('[handleValueChange] called with:', newValue, 'current value:', value);

    if (!multiple) {
      onValueChange?.(newValue);
      return;
    }

    // Special handling for "All" option - just select all
    if (newValue === 'all') {
      console.log('[handleValueChange] All clicked, setting to: all');
      onValueChange?.('all');
      return;
    }

    // Toggle individual item in/out of selection
    const isSelected = selectedValues.includes(newValue);
    const newSelected = isSelected
      ? selectedValues.filter(v => v !== newValue)
      : [...selectedValues, newValue];

    // Convert back to comma-separated string
    // If all options are selected, use "all"
    const allOptions = props.options?.map(opt => opt.value) || [];
    const allSelected = allOptions.length > 0 && allOptions.every(opt => newSelected.includes(opt));
    const newValueString = newSelected.length === 0 ? '' : allSelected ? 'all' : newSelected.join(',');
    onValueChange?.(newValueString);
  }, [multiple, selectedValues, onValueChange, props.options, value]);

  // Memoize context value to ensure proper re-renders
  const contextValue = React.useMemo(() => ({
    multiple: multiple || false,
    selectedValues,
    options: props.options || [],
    value
  }), [multiple, selectedValues, props.options, value]);

  if (multiple) {
    return (
      <MultiSelectContext.Provider value={contextValue}>
        <SelectPrimitive.Root
          data-slot="select"
          {...props}
          value={value}
          onValueChange={handleValueChange}
          open={open}
          onOpenChange={setOpen}
        >
          {children}
        </SelectPrimitive.Root>
      </MultiSelectContext.Provider>
    );
  }

  return <SelectPrimitive.Root data-slot="select" value={value} onValueChange={onValueChange} {...props}>{children}</SelectPrimitive.Root>
}

function SelectGroup({
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Group>) {
  return <SelectPrimitive.Group data-slot="select-group" {...props} />
}

function SelectValue({
  placeholder,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Value>) {
  const context = React.useContext(MultiSelectContext);

  if (context?.multiple) {
    const { selectedValues, options, value } = context;

    // Check value prop first - if "all", display "All"
    const displayValue = value === 'all'
      ? 'All'
      : !value || selectedValues.length === 0
      ? placeholder || 'Select...'
      : selectedValues.length === 1
      ? options.find(opt => opt.value === selectedValues[0])?.label || selectedValues[0]
      : `${selectedValues.length} selected`;

    return <span data-slot="select-value" suppressHydrationWarning>{displayValue}</span>;
  }

  return <SelectPrimitive.Value data-slot="select-value" placeholder={placeholder} {...props} />
}

function SelectTrigger({
  className,
  size = "default",
  children,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Trigger> & {
  size?: "sm" | "default"
}) {
  return (
    <SelectPrimitive.Trigger
      data-slot="select-trigger"
      data-size={size}
      className={cn(
        "border-input data-[placeholder]:text-muted-foreground [&_svg:not([class*='text-'])]:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 dark:hover:bg-input/50 flex w-fit items-center justify-between gap-2 rounded-md border bg-transparent px-3 py-2 text-sm whitespace-nowrap shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 data-[size=default]:h-9 data-[size=sm]:h-8 *:data-[slot=select-value]:line-clamp-1 *:data-[slot=select-value]:flex *:data-[slot=select-value]:items-center *:data-[slot=select-value]:gap-2 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}
    >
      {children}
      <SelectPrimitive.Icon asChild>
        <ChevronDownIcon className="size-4 opacity-50" />
      </SelectPrimitive.Icon>
    </SelectPrimitive.Trigger>
  )
}

function SelectContent({
  className,
  children,
  position = "popper",
  align = "center",
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Content>) {
  const context = React.useContext(MultiSelectContext);

  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content
        data-slot="select-content"
        className={cn(
          "bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 relative z-50 max-h-(--radix-select-content-available-height) min-w-[8rem] origin-(--radix-select-content-transform-origin) overflow-x-hidden overflow-y-auto rounded-md border shadow-md",
          position === "popper" &&
            "data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1",
          className
        )}
        position={position}
        align={align}
        onCloseAutoFocus={(e) => {
          // Prevent auto-close in multi-select mode
          if (context?.multiple) {
            e.preventDefault();
          }
        }}
        {...props}
      >
        <SelectScrollUpButton />
        <SelectPrimitive.Viewport
          className={cn(
            "p-1",
            position === "popper" &&
              "h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)] scroll-my-1"
          )}
        >
          {children}
        </SelectPrimitive.Viewport>
        <SelectScrollDownButton />
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  )
}

function SelectLabel({
  className,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Label>) {
  return (
    <SelectPrimitive.Label
      data-slot="select-label"
      className={cn("text-muted-foreground px-2 py-1.5 text-xs", className)}
      {...props}
    />
  )
}

function SelectItem({
  className,
  children,
  value,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Item>) {
  const context = React.useContext(MultiSelectContext);

  // In multi-select mode, check if this item is selected
  let isSelected = false;
  if (context?.multiple) {
    // Debug logging
    console.log('[SelectItem]', value, 'context.value:', context.value);

    // Special handling for "All" option - it's selected only when value='all'
    if (value === 'all') {
      isSelected = context.value === 'all';
    } else {
      // Regular items - check if value='all' (all selected) OR this value is in the comma-separated list
      if (context.value === 'all') {
        isSelected = true;
      } else if (!context.value || context.value === '') {
        // Explicitly handle empty value - nothing selected
        isSelected = false;
      } else {
        const selectedList = context.value.split(',').map(v => v.trim().toLowerCase());
        isSelected = selectedList.includes(value || '');
      }
    }

    console.log('[SelectItem]', value, 'isSelected:', isSelected);
  }

  return (
    <SelectPrimitive.Item
      data-slot="select-item"
      value={value}
      className={cn(
        "focus:bg-accent focus:text-accent-foreground [&_svg:not([class*='text-'])]:text-muted-foreground relative flex w-full cursor-default items-center gap-2 rounded-sm py-1.5 pr-8 pl-2 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4 *:[span]:last:flex *:[span]:last:items-center *:[span]:last:gap-2",
        className
      )}
      {...props}
    >
      <span className="absolute right-2 flex size-3.5 items-center justify-center">
        {context?.multiple ? (
          // In multi-select mode, show check for selected items
          isSelected && <CheckIcon className="size-4" />
        ) : (
          // In single-select mode, use the ItemIndicator
          <SelectPrimitive.ItemIndicator>
            <CheckIcon className="size-4" />
          </SelectPrimitive.ItemIndicator>
        )}
      </span>
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  )
}

function SelectSeparator({
  className,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Separator>) {
  return (
    <SelectPrimitive.Separator
      data-slot="select-separator"
      className={cn("bg-border pointer-events-none -mx-1 my-1 h-px", className)}
      {...props}
    />
  )
}

function SelectScrollUpButton({
  className,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.ScrollUpButton>) {
  return (
    <SelectPrimitive.ScrollUpButton
      data-slot="select-scroll-up-button"
      className={cn(
        "flex cursor-default items-center justify-center py-1",
        className
      )}
      {...props}
    >
      <ChevronUpIcon className="size-4" />
    </SelectPrimitive.ScrollUpButton>
  )
}

function SelectScrollDownButton({
  className,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.ScrollDownButton>) {
  return (
    <SelectPrimitive.ScrollDownButton
      data-slot="select-scroll-down-button"
      className={cn(
        "flex cursor-default items-center justify-center py-1",
        className
      )}
      {...props}
    >
      <ChevronDownIcon className="size-4" />
    </SelectPrimitive.ScrollDownButton>
  )
}

export {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectScrollDownButton,
  SelectScrollUpButton,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
}
