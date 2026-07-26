import { useGetUserProfile, getGetUserProfileQueryKey, useUpdateUserProfile } from "@workspace/api-client-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { useState, useEffect } from "react";
import {
  INCOME_OPTIONS,
  SECTOR_OPTIONS,
  INVESTMENT_OPTIONS,
  CITY_OPTIONS,
  sectorsToArray,
  sectorsToString,
} from "@/lib/profile-vocab";

export default function Profile() {
  const userId = "default_user";
  const { data: profile, isLoading } = useGetUserProfile({ user_id: userId }, {
    query: { queryKey: getGetUserProfileQueryKey({ user_id: userId }) }
  });
  
  const updateProfile = useUpdateUserProfile();
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    income_type: "",
    sector_exposure: "",
    investment_profile: "",
    city: "",
    companies_of_interest: ""
  });

  useEffect(() => {
    if (profile) {
      setFormData({
        income_type: profile.income_type || "",
        sector_exposure: profile.sector_exposure || "",
        investment_profile: profile.investment_profile || "",
        city: profile.city || "",
        companies_of_interest: profile.companies_of_interest || ""
      });
    }
  }, [profile]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile.mutate({ data: { user_id: userId, ...formData } }, {
      onSuccess: () => {
        toast({
          title: "Profile Updated",
          description: "Your personal impact analysis will refresh on the next card load.",
        });
      },
      // Without this, a failing save was completely invisible: the PUT/POST verb
      // mismatch returned 405 on every submit for months and the UI said nothing.
      onError: (err: unknown) => {
        toast({
          variant: "destructive",
          title: "Could not save profile",
          description: err instanceof Error ? err.message : "The server rejected the request.",
        });
      },
    });
  };

  const selectedSectors = sectorsToArray(formData.sector_exposure);

  const toggleSector = (sector: string) => {
    const next = selectedSectors.includes(sector)
      ? selectedSectors.filter((s) => s !== sector)
      : [...selectedSectors, sector];
    setFormData((p) => ({ ...p, sector_exposure: sectorsToString(next) }));
  };

  return (
    <div className="p-6 md:p-8 max-w-2xl mx-auto h-full overflow-y-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-display font-bold tracking-tight">Intelligence Profile</h1>
        <p className="text-muted-foreground text-sm">Calibrate your feed's personal impact analysis.</p>
      </header>

      {isLoading ? (
        <div className="space-y-6">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6 bg-card border border-border p-6 rounded-xl">
          <div className="space-y-2">
            <Label className="font-mono text-xs text-muted-foreground">INCOME TYPE</Label>
            <Select value={formData.income_type} onValueChange={(val) => setFormData(p => ({...p, income_type: val}))}>
              <SelectTrigger>
                <SelectValue placeholder="Select primary income source" />
              </SelectTrigger>
              <SelectContent>
                {INCOME_OPTIONS.map((opt) => (
                  <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="font-mono text-xs text-muted-foreground">INVESTMENT PROFILE</Label>
            <Select value={formData.investment_profile} onValueChange={(val) => setFormData(p => ({...p, investment_profile: val}))}>
              <SelectTrigger>
                <SelectValue placeholder="Select risk tolerance" />
              </SelectTrigger>
              <SelectContent>
                {INVESTMENT_OPTIONS.map((opt) => (
                  <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="font-mono text-xs text-muted-foreground">SECTOR EXPOSURE</Label>
            <div className="flex flex-wrap gap-2">
              {SECTOR_OPTIONS.map((sector) => {
                const active = selectedSectors.includes(sector);
                return (
                  <button
                    key={sector}
                    type="button"
                    onClick={() => toggleSector(sector)}
                    aria-pressed={active}
                    className={`rounded-full border px-3 py-1.5 text-xs transition-colors ${
                      active
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border text-muted-foreground hover:border-primary/40"
                    }`}
                  >
                    {sector}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <Label className="font-mono text-xs text-muted-foreground">CITY</Label>
            <Select value={formData.city} onValueChange={(val) => setFormData(p => ({...p, city: val}))}>
              <SelectTrigger>
                <SelectValue placeholder="Select your city" />
              </SelectTrigger>
              <SelectContent>
                {CITY_OPTIONS.map((opt) => (
                  <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="font-mono text-xs text-muted-foreground">COMPANIES OF INTEREST (Comma separated)</Label>
            <Textarea 
              value={formData.companies_of_interest} 
              onChange={(e) => setFormData(p => ({...p, companies_of_interest: e.target.value}))}
              placeholder="Apple, Tesla, Reliance, TSMC..."
              className="resize-none h-24"
            />
          </div>

          <div className="pt-4 border-t border-border flex justify-end">
            <Button type="submit" disabled={updateProfile.isPending} className="font-mono text-xs px-8">
              {updateProfile.isPending ? "SAVING..." : "SAVE PROFILE"}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}