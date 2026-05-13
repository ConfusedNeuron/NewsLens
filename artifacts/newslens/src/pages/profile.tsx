import { useGetUserProfile, getGetUserProfileQueryKey, useUpdateUserProfile } from "@workspace/api-client-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { useState, useEffect } from "react";

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
          description: "Your intelligence filters have been recalibrated.",
        });
      }
    });
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
                <SelectItem value="salary">Salary (W2/PAYE)</SelectItem>
                <SelectItem value="business">Business Owner</SelectItem>
                <SelectItem value="freelance">Freelance / Contractor</SelectItem>
                <SelectItem value="investments">Investments / Passive</SelectItem>
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
                <SelectItem value="conservative">Conservative</SelectItem>
                <SelectItem value="moderate">Moderate</SelectItem>
                <SelectItem value="aggressive">Aggressive</SelectItem>
                <SelectItem value="crypto_heavy">Crypto Heavy</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label className="font-mono text-xs text-muted-foreground">SECTOR EXPOSURE</Label>
              <Input 
                value={formData.sector_exposure} 
                onChange={(e) => setFormData(p => ({...p, sector_exposure: e.target.value}))}
                placeholder="e.g. Tech, Real Estate"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="font-mono text-xs text-muted-foreground">CITY</Label>
              <Input 
                value={formData.city} 
                onChange={(e) => setFormData(p => ({...p, city: e.target.value}))}
                placeholder="e.g. San Francisco"
              />
            </div>
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