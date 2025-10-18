from typing import Dict, List, TypedDict, Optional, Tuple
from pydantic import Field
from pydantic import BaseModel


class UserRequest(BaseModel):
    coinName: str
    amountUSD: float
    investmentStartDate: str
    investmentDurationMonths: int


class TradingFees(BaseModel):
    taker_fee: float
    maker_fee: float


class PlatformData(BaseModel):
    current_price: float
    trust_score: int
    avg_spread_pct: float
    trading_fees: TradingFees
    deposit_withdraw_options: List[str]


class Platforms(BaseModel):
    Binance: PlatformData
    Coinbase: PlatformData


class ExchangeComparison(BaseModel):
    platforms: Platforms


class FinanceMetrics(TypedDict):
    cagr: str
    volatility: str
    max_drawdown: str


class InvestmentAdvice(BaseModel):
    should_invest: str   # "Yes" or "No"
    reason: str          # concise reason


class RecommendedPlatform(BaseModel):
    platform_name: str   # e.g., "Binance", "Coinbase"
    reason: str          # reason for choosing this platform


class CurrentPrice(BaseModel):
    Binance: float
    Coinbase: float
    cheaper_platform: str  # "Binance" or "Coinbase"


class CryptoAdvice(BaseModel):
    coinSymbol: str
    current_price: CurrentPrice
    final_advice: str
    investment_advice: InvestmentAdvice
    recommended_platform: RecommendedPlatform
    risk_assessment: str


class EstimatedReturns(BaseModel):
    future_value_nominal_usd: float
    future_value_real_usd: float
    best_case_volatility_usd: float
    worst_case_volatility_usd: float
    drawdown_floor_usd: float


# class FinalEstimates(BaseModel):
#     future_value_nominal_usd: float
#     future_value_real_usd: float
#     best_case_volatility_usd: float
#     worst_case_volatility_usd: float
#     drawdown_floor_usd: float


# class EstimatedReturns(BaseModel):
#     timeline: List[dict]   # or make another model if timeline has a structure
#     final_estimates: FinalEstimates


class CryptoAdvicerResponse(BaseModel):
    advice: CryptoAdvice
    estimated_returns: EstimatedReturns


# NFT
class NFTRequest(BaseModel):
    userPrompt: str
    nftName: str
    nftCollectionName: str
    socialMediaPlatform: str


class NFTAttribute(BaseModel):
    trait_type: str
    value: str


class NFTMetadata(BaseModel):
    name: str
    description: str
    image: str
    attributes: List[NFTAttribute]


class NFTMarketingContent(BaseModel):
    tagline: str
    promotional_post: str


class NFTResponse(BaseModel):
    nftPrompt: str
    nftURL: str
    nftMetaData: NFTMetadata
    nftSocialMediaPost: NFTMarketingContent


class AdviseRequest(BaseModel):
    coin: str = Field(..., description="Token symbol, e.g., SOL/BTC/ETH/USDC")
    amount_usd: Optional[float] = Field(None, description="Optional amount for projection")
    start_date: Optional[str] = Field(None, description="dd/mm/yyyy (optional)")
    duration_months: Optional[int] = Field(3, description="Investment duration in months")
    risk: Optional[str] = Field("low", pattern="^(low|medium|high)$")
    chain: Optional[str] = Field("Polygon")
    min_tvl_usd: Optional[float] = Field(1_000_000)
    include_rewards: Optional[bool] = Field(True)
    compare_protocols: Optional[Tuple[str, str]] = Field(("aave", "compound"))