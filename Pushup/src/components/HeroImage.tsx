import heroPushupImage from "../assets/hero-pushup.png";

export default function HeroImage() {
  return (
    <div className="mx-4 mt-3 rounded-2xl overflow-hidden h-[130px] relative bg-gradient-to-br from-[#2a1810] via-[#1a1010] to-[#0a0505]">
      <img
        src={heroPushupImage}
        alt="Athlete doing pushups"
        className="absolute inset-0 w-full h-full object-cover"
      />
    </div>
  );
}
